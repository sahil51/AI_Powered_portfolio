import json
import time
from collections.abc import Sequence
from typing import Any

import redis.asyncio as aioredis

from infrastructure.cache.key_builder import default_key_builder


class IdempotencyStore:
    def __init__(self, redis: aioredis.Redis, default_ttl: int = 3600) -> None:
        self._redis = redis
        self._default_ttl = default_ttl

    async def is_duplicate(self, idempotency_key: str) -> bool:
        key = default_key_builder.idempotency(idempotency_key)
        return await self._redis.exists(key) > 0

    async def mark_processed(
        self,
        idempotency_key: str,
        response: Any = None,
        ttl: int | None = None,
    ) -> None:
        key = default_key_builder.idempotency(idempotency_key)
        data = {
            "timestamp": time.time(),
            "response": response,
        }
        await self._redis.setex(key, ttl or self._default_ttl, json.dumps(data, default=str))

    async def get_response(self, idempotency_key: str) -> Any | None:
        key = default_key_builder.idempotency(idempotency_key)
        raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            data = json.loads(raw)
            return data.get("response")
        except (json.JSONDecodeError, AttributeError):
            return None

    async def is_first_attempt(self, idempotency_key: str) -> bool:
        return not await self.is_duplicate(idempotency_key)

    async def cleanup_expired(self, batch_size: int = 100) -> int:
        cursor = 0
        cleaned = 0
        pattern = default_key_builder.idempotency("*")
        while True:
            cursor, keys = await self._redis.scan(cursor=cursor, match=pattern, count=batch_size)
            for key in keys:
                ttl = await self._redis.ttl(key)
                if ttl <= 0:
                    await self._redis.delete(key)
                    cleaned += 1
            if cursor == 0:
                break
        return cleaned

    async def bulk_check(self, idempotency_keys: Sequence[str]) -> dict[str, bool]:
        keys = [default_key_builder.idempotency(k) for k in idempotency_keys]
        raw_values = await self._redis.mget(keys)
        result: dict[str, bool] = {}
        for key, raw in zip(idempotency_keys, raw_values, strict=False):
            result[key] = raw is not None
        return result
