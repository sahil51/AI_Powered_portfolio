import json
import time
from typing import Any

import redis.asyncio as aioredis

from infrastructure.cache.key_builder import default_key_builder


class SessionStore:
    def __init__(self, redis: aioredis.Redis, default_ttl: int = 3600) -> None:
        self._redis = redis
        self._default_ttl = default_ttl

    async def create_session(self, session_id: str, data: dict[str, Any], ttl: int | None = None) -> None:
        key = default_key_builder.session(session_id)
        payload = {
            "data": data,
            "created_at": time.time(),
            "last_access": time.time(),
        }
        await self._redis.setex(key, ttl or self._default_ttl, json.dumps(payload, default=str))

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        key = default_key_builder.session(session_id)
        raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            payload = json.loads(raw)
            payload["last_access"] = time.time()
            await self._redis.expire(key, self._default_ttl)
            return payload.get("data", {})
        except (json.JSONDecodeError, AttributeError):
            return None

    async def update_session(self, session_id: str, data: dict[str, Any], ttl: int | None = None) -> None:
        key = default_key_builder.session(session_id)
        payload = {
            "data": data,
            "last_access": time.time(),
        }
        await self._redis.setex(key, ttl or self._default_ttl, json.dumps(payload, default=str))

    async def delete_session(self, session_id: str) -> None:
        key = default_key_builder.session(session_id)
        await self._redis.delete(key)

    async def session_exists(self, session_id: str) -> bool:
        key = default_key_builder.session(session_id)
        return await self._redis.exists(key) > 0

    async def refresh_session(self, session_id: str, ttl: int | None = None) -> bool:
        key = default_key_builder.session(session_id)
        if await self._redis.exists(key):
            await self._redis.expire(key, ttl or self._default_ttl)
            return True
        return False

    async def touch(self, session_id: str) -> None:
        key = default_key_builder.session(session_id)
        await self._redis.expire(key, self._default_ttl)

    async def get_ttl(self, session_id: str) -> int:
        key = default_key_builder.session(session_id)
        return await self._redis.ttl(key)


class ConversationSessionStore(SessionStore):
    def __init__(self, redis: aioredis.Redis, default_ttl: int = 86400) -> None:
        super().__init__(redis, default_ttl)

    async def create_conversation(self, conversation_id: str, context: dict[str, Any]) -> None:
        await self.create_session(f"conv:{conversation_id}", context)

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        return await self.get_session(f"conv:{conversation_id}")

    async def update_conversation(self, conversation_id: str, context: dict[str, Any]) -> None:
        await self.update_session(f"conv:{conversation_id}", context)

    async def delete_conversation(self, conversation_id: str) -> None:
        await self.delete_session(f"conv:{conversation_id}")


class TemporaryContextStore(SessionStore):
    def __init__(self, redis: aioredis.Redis, default_ttl: int = 300) -> None:
        super().__init__(redis, default_ttl)

    async def set_temp(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self.create_session(f"tmp:{key}", {"value": value}, ttl)

    async def get_temp(self, key: str) -> Any | None:
        data = await self.get_session(f"tmp:{key}")
        if data is None:
            return None
        return data.get("value")
