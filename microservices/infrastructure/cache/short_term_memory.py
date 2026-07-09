import json
from typing import Any

import redis.asyncio as aioredis

from infrastructure.cache.key_builder import default_key_builder


class ConversationCache:
    def __init__(self, redis: aioredis.Redis, default_ttl: int = 86400) -> None:
        self._redis = redis
        self._default_ttl = default_ttl

    async def set_state(self, conversation_id: str, state: dict[str, Any]) -> None:
        key = default_key_builder.memory(conversation_id, "state")
        await self._redis.setex(key, self._default_ttl, json.dumps(state, default=str))

    async def get_state(self, conversation_id: str) -> dict[str, Any] | None:
        key = default_key_builder.memory(conversation_id, "state")
        raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def delete_state(self, conversation_id: str) -> None:
        key = default_key_builder.memory(conversation_id, "state")
        await self._redis.delete(key)


class StateCache:
    def __init__(self, redis: aioredis.Redis, default_ttl: int = 3600) -> None:
        self._redis = redis
        self._default_ttl = default_ttl

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        full_key = default_key_builder.memory("state_cache", key)
        await self._redis.setex(full_key, ttl or self._default_ttl, json.dumps(value, default=str))

    async def get(self, key: str) -> Any | None:
        full_key = default_key_builder.memory("state_cache", key)
        raw = await self._redis.get(full_key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def delete(self, key: str) -> None:
        full_key = default_key_builder.memory("state_cache", key)
        await self._redis.delete(full_key)


class TemporaryMemory:
    def __init__(self, redis: aioredis.Redis, default_ttl: int = 300) -> None:
        self._redis = redis
        self._default_ttl = default_ttl

    async def remember(self, key: str, value: Any, ttl: int | None = None) -> None:
        full_key = default_key_builder.memory("tmp", key)
        await self._redis.setex(full_key, ttl or self._default_ttl, json.dumps(value, default=str))

    async def recall(self, key: str) -> Any | None:
        full_key = default_key_builder.memory("tmp", key)
        raw = await self._redis.get(full_key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def forget(self, key: str) -> None:
        full_key = default_key_builder.memory("tmp", key)
        await self._redis.delete(full_key)

    async def remember_batch(self, mapping: dict[str, Any], ttl: int | None = None) -> None:
        pipe = self._redis.pipeline()
        for key, value in mapping.items():
            full_key = default_key_builder.memory("tmp", key)
            pipe.setex(full_key, ttl or self._default_ttl, json.dumps(value, default=str))
        await pipe.execute()
