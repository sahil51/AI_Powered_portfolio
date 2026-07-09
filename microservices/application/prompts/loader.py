from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path

from application.prompts.exceptions import PromptLoadError


class PromptLoader(ABC):
    @abstractmethod
    async def load(self, path: str) -> tuple[str, str]:
        ...

    @abstractmethod
    async def exists(self, path: str) -> bool:
        ...

    @abstractmethod
    async def list_paths(self, directory: str) -> list[str]:
        ...


class FilesystemPromptLoader(PromptLoader):
    def __init__(self, base_path: str | None = None) -> None:
        self._base_path = Path(base_path) if base_path else Path("prompts")

    async def load(self, path: str) -> tuple[str, str]:
        full_path = self._base_path / path
        if not full_path.exists():
            raise PromptLoadError(f"Prompt file not found: {full_path}")
        try:
            content = full_path.read_text(encoding="utf-8")
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            return content, content_hash
        except Exception as e:
            raise PromptLoadError(f"Failed to load prompt: {full_path}: {e}")

    async def exists(self, path: str) -> bool:
        full_path = self._base_path / path
        return full_path.exists()

    async def list_paths(self, directory: str) -> list[str]:
        full_dir = self._base_path / directory
        if not full_dir.exists() or not full_dir.is_dir():
            return []
        return [str(p.relative_to(self._base_path)) for p in full_dir.glob("*_v*.md")]
