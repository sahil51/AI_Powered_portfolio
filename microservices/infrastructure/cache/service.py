import gzip
import json
from collections.abc import Sequence
from typing import Any

import redis.asyncio as aioredis

from infrastructure.cache.key_builder import KeyBuilder, default_key_builder


class CacheService:
    def __init__(
        self,
        redis: aioredis.Redis,
        key_builder: KeyBuilder | None = None,
        default_ttl: int = 86400,
        enable_compression: bool = False,
        compression_threshold: int = 1024,
    ) -> None:
        self._redis = redis
        self._key_builder = key_builder or default_key_builder
        self._default_ttl = default_ttl
        self._enable_compression = enable_compression
        self._compression_threshold = compression_threshold
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Any | None:
        raw = await self._redis.get(key)
        if raw is None:
            self._misses += 1
            return None
        self._hits += 1
        return self._deserialize(raw)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        compress: bool | None = None,
    ) -> None:
        ttl = ttl if ttl is not None else self._default_ttl
        raw = self._serialize(value, compress)
        await self._redis.setex(key, ttl, raw)

    async def set_many(self, mapping: dict[str, Any], ttl: int | None = None) -> None:
        pipe = self._redis.pipeline()
        for key, value in mapping.items():
            raw = self._serialize(value)
            pipe.setex(key, ttl or self._default_ttl, raw)
        await pipe.execute()

    async def get_many(self, keys: Sequence[str]) -> dict[str, Any]:
        raw_values = await self._redis.mget(list(keys))
        result: dict[str, Any] = {}
        for key, raw in zip(keys, raw_values, strict=False):
            if raw is not None:
                self._hits += 1
                result[key] = self._deserialize(raw)
            else:
                self._misses += 1
        return result

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def delete_many(self, keys: Sequence[str]) -> None:
        if keys:
            await self._redis.delete(*keys)

    async def delete_pattern(self, pattern: str) -> int:
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await self._redis.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await self._redis.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        return deleted

    async def exists(self, key: str) -> bool:
        return await self._redis.exists(key) > 0

    async def increment(self, key: str, amount: int = 1, ttl: int | None = None) -> int:
        value = await self._redis.incr(key, amount)
        if ttl is not None:
            await self._redis.expire(key, ttl)
        return value

    async def expire(self, key: str, ttl: int) -> None:
        await self._redis.expire(key, ttl)

    async def ttl(self, key: str) -> int:
        return await self._redis.ttl(key)

    async def clear_namespace(self, namespace: str) -> int:
        pattern = self._key_builder.build("*", prefix=namespace)
        return await self.delete_pattern(pattern)

    async def touch(self, key: str, ttl: int | None = None) -> None:
        ttl = ttl if ttl is not None else self._default_ttl
        await self._redis.expire(key, ttl)

    def _serialize(self, value: Any, compress: bool | None = None) -> bytes:
        encoded = json.dumps(value, default=str).encode("utf-8")
        should_compress = (
            compress if compress is not None else (
                self._enable_compression and len(encoded) > self._compression_threshold
            )
        )
        if should_compress:
            return gzip.compress(encoded)
        return encoded

    def _deserialize(self, raw: bytes) -> Any:
        try:
            if isinstance(raw, bytes) and len(raw) > 0 and raw[0] == 0x1f:
                raw = gzip.decompress(raw)
            return json.loads(raw)
        except (json.JSONDecodeError, gzip.BadGzipFile):
            return raw.decode("utf-8") if isinstance(raw, bytes) else raw

    @property
    def stats(self) -> dict[str, int]:
        return {"hits": self._hits, "misses": self._misses}

    @property
    def hit_ratio(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def miss_ratio(self) -> float:
        return 1.0 - self.hit_ratio

    def reset_stats(self) -> None:
        self._hits = 0
        self._misses = 0
