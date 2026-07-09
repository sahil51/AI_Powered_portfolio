from typing import Any

from infrastructure.cache.connection import redis_manager
from infrastructure.cache.key_builder import default_key_builder


class IdentityCache:
    def __init__(self, default_ttl: int = 3600) -> None:
        self._default_ttl = default_ttl

    async def cache_identity(self, user_id: str, data: dict[str, Any]) -> None:
        key = default_key_builder.build("identity", user_id)
        await redis_manager.client.hset(key, mapping=data)
        await redis_manager.client.expire(key, self._default_ttl)

    async def get_cached_identity(self, user_id: str) -> dict[str, Any] | None:
        key = default_key_builder.build("identity", user_id)
        data = await redis_manager.client.hgetall(key)
        return data if data else None

    async def invalidate_identity(self, user_id: str) -> None:
        key = default_key_builder.build("identity", user_id)
        await redis_manager.client.delete(key)

    async def cache_session(self, session_id: str, user_id: str) -> None:
        key = default_key_builder.build("session", session_id)
        await redis_manager.client.setex(key, self._default_ttl, user_id)

    async def get_session_user(self, session_id: str) -> str | None:
        key = default_key_builder.build("session", session_id)
        value = await redis_manager.client.get(key)
        return value if isinstance(value, str) else None

    async def merge_identity_data(self, source_id: str, target_id: str) -> None:
        source_key = default_key_builder.build("identity", source_id)
        target_key = default_key_builder.build("identity", target_id)
        source_data = await redis_manager.client.hgetall(source_key)
        if source_data:
            await redis_manager.client.hset(target_key, mapping=source_data)
            await redis_manager.client.expire(target_key, self._default_ttl)
            await redis_manager.client.delete(source_key)
