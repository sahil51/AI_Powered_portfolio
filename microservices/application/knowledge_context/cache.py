from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from application.knowledge_context.exceptions import ContextCacheError
from application.knowledge_context.interfaces import ContextCacheStrategy
from application.knowledge_context.models import KnowledgeContextResult
from infrastructure.cache.redis_client import CacheService


class KnowledgeContextCache(ContextCacheStrategy):
    def __init__(
        self,
        cache_service: CacheService,
        default_ttl: int = 300,
        retrieval_ttl: int = 60,
        compression_ttl: int = 600,
    ) -> None:
        self._cache = cache_service
        self._default_ttl = default_ttl
        self._retrieval_ttl = retrieval_ttl
        self._compression_ttl = compression_ttl

    def _make_key(self, prefix: str, *parts: str) -> str:
        raw = ":".join(parts)
        return f"knowledge:context:{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"

    def _make_version_key(self, document_id: str) -> str:
        return f"knowledge:context:version:{document_id}"

    async def get(self, key: str) -> Any | None:
        try:
            data = await self._cache.get(key)
            if data is None:
                return None
            if isinstance(data, str):
                return json.loads(data)
            return data
        except Exception as e:
            raise ContextCacheError(f"Cache get failed: {e}") from e

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        try:
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            await self._cache.set(key, value, ttl=ttl)
        except Exception as e:
            raise ContextCacheError(f"Cache set failed: {e}") from e

    async def delete(self, key: str) -> None:
        try:
            await self._cache.delete(key)
        except Exception as e:
            raise ContextCacheError(f"Cache delete failed: {e}") from e

    async def invalidate_for_document(self, document_id: str) -> None:
        try:
            version_key = self._make_version_key(document_id)
            new_version = str(time.time())
            await self._cache.set(version_key, new_version, ttl=86400)
        except Exception as e:
            raise ContextCacheError(f"Cache invalidation failed: {e}") from e

    async def get_or_compute(
        self,
        key: str,
        compute: Any,
        ttl: int = 300,
    ) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        result = await compute() if callable(compute) else compute
        await self.set(key, result, ttl=ttl)
        return result

    async def cache_retrieval_result(
        self,
        query: str,
        config_hash: str,
        result: KnowledgeContextResult,
    ) -> str:
        key = self._make_key("retrieval", query, config_hash)
        await self.set(key, result, ttl=self._retrieval_ttl)
        return key

    async def get_retrieval_result(
        self,
        query: str,
        config_hash: str,
    ) -> KnowledgeContextResult | None:
        key = self._make_key("retrieval", query, config_hash)
        return await self.get(key)

    async def clear(self) -> None:
        pass
