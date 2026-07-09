from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from application.prompts.cache import PromptCache
from application.prompts.exceptions import PromptVersionNotFoundError
from application.prompts.loader import FilesystemPromptLoader, PromptLoader
from application.prompts.metadata import PromptMetadata, PromptStatus
from application.prompts.metrics import PromptMetrics
from application.prompts.renderer import PromptRenderer
from application.prompts.validator import PromptValidator
from application.prompts.version import PromptVersion

logger = logging.getLogger("ai_assistant")


class PromptRegistry:
    def __init__(
        self,
        loader: PromptLoader | None = None,
        renderer: PromptRenderer | None = None,
        validator: PromptValidator | None = None,
        cache: PromptCache | None = None,
    ) -> None:
        self._loader = loader or FilesystemPromptLoader()
        self._renderer = renderer or PromptRenderer(strict=True)
        self._validator = validator or PromptValidator()
        self._cache = cache
        self._registry: dict[str, PromptMetadata] = {}
        self._versions: dict[str, list[PromptVersion]] = {}
        self._versions_latest: dict[str, str] = {}
        self._metrics = PromptMetrics()

    async def load_registry(self) -> int:
        count = 0
        for category in ["system", "meeting", "classification", "memory", "analysis", "workflow", "tool", "rag"]:
            paths = await self._loader.list_paths(category)
            for path in paths:
                try:
                    await self._load_prompt(path, category)
                    count += 1
                except Exception as e:
                    logger.warning("Failed to load prompt %s: %s", path, e)
        logger.info("Loaded %d prompts into registry", count)
        return count

    async def _load_prompt(self, path: str, category: str) -> None:
        content, content_hash = await self._loader.load(path)
        normalized = path.replace("\\", "/").replace(".md", "")
        parts = normalized.split("/")
        stem = parts[-1]
        import re
        stem_no_ver = re.sub(r"_v\d+$", "", stem)
        parts[-1] = stem_no_ver
        name = ".".join(parts)
        version = self._extract_version(path)
        metadata = PromptMetadata(
            name=name,
            category=category,
            version=version,
            status=PromptStatus.ACTIVE,
            content_hash=content_hash,
            content_path=path,
        )
        self._registry[name] = metadata
        ver = PromptVersion(
            version=version,
            content=content,
            content_hash=content_hash,
        )
        if name not in self._versions:
            self._versions[name] = []
        self._versions[name].append(ver)
        self._versions_latest[name] = version
        self._metrics.record_load()

    def _extract_version(self, path: str) -> str:
        import re
        match = re.search(r"_v(\d+)", path)
        if match:
            return f"{match.group(1)}.0.0"
        return "1.0.0"

    async def get(self, name: str, version: str | None = None) -> str:
        if self._cache:
            cached = await self._cache.get(name, version)
            if cached is not None:
                self._metrics.record_cache_hit()
                return cached
            self._metrics.record_cache_miss()

        ver = self._resolve_version(name, version)
        if ver is None:
            raise PromptVersionNotFoundError(f"Version {version} not found for prompt '{name}'")
        content = ver.content

        if self._cache:
            await self._cache.set(name, content, version)

        self._metrics.record_load()
        return content

    def _resolve_version(self, name: str, version: str | None = None) -> PromptVersion | None:
        if name not in self._versions:
            return None
        if version is None:
            latest_ver = self._versions_latest.get(name)
            for v in self._versions[name]:
                if v.version == latest_ver:
                    return v
            return self._versions[name][-1] if self._versions[name] else None
        for v in self._versions[name]:
            if v.version == version:
                return v
        return None

    async def render(self, name: str, variables: dict[str, Any], version: str | None = None) -> str:
        template = await self.get(name, version)
        return self._renderer.render(template, variables)

    def list_prompts(self, category: str | None = None) -> list[PromptMetadata]:
        if category:
            return [m for m in self._registry.values() if m.category == category]
        return list(self._registry.values())

    def get_metadata(self, name: str) -> PromptMetadata | None:
        return self._registry.get(name)

    def get_version_history(self, name: str) -> list[PromptVersion]:
        return self._versions.get(name, [])

    def get_latest_version(self, name: str) -> str | None:
        return self._versions_latest.get(name)

    async def register_prompt(
        self,
        name: str,
        category: str,
        content: str,
        version: str = "1.0.0",
        status: PromptStatus = PromptStatus.DRAFT,
    ) -> PromptMetadata:
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        metadata = PromptMetadata(
            name=name,
            category=category,
            version=version,
            status=status,
            content_hash=content_hash,
            content_path=f"{category}/{name}_v{version.replace('.', '_')}.md",
        )
        self._registry[name] = metadata
        ver = PromptVersion(version=version, content=content, content_hash=content_hash)
        if name not in self._versions:
            self._versions[name] = []
        self._versions[name].append(ver)
        self._versions_latest[name] = version
        self._metrics.record_registration()
        return metadata

    def deprecate(self, name: str) -> bool:
        metadata = self._registry.get(name)
        if metadata is None:
            return False
        metadata.status = PromptStatus.DEPRECATED
        metadata.deprecated_at = datetime.now(timezone.utc)
        return True

    def activate(self, name: str, version: str) -> bool:
        metadata = self._registry.get(name)
        if metadata is None:
            return False
        metadata.status = PromptStatus.ACTIVE
        self._versions_latest[name] = version
        return True

    @property
    def count(self) -> int:
        return len(self._registry)

    @property
    def metrics(self) -> PromptMetrics:
        return self._metrics
