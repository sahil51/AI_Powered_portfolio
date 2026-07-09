import uuid

from infrastructure.cache.connection import redis_manager
from infrastructure.cache.key_builder import default_key_builder


class SessionManager:
    def __init__(self, default_ttl: int = 3600) -> None:
        self._default_ttl = default_ttl

    async def get_or_create(self, session_id: str | None = None) -> str:
        if session_id and await self.session_exists(session_id):
            await self.refresh_session(session_id)
            return session_id
        return await self.create_session()

    async def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        key = default_key_builder.build("session", session_id)
        await redis_manager.client.setex(key, self._default_ttl, session_id)
        return session_id

    async def session_exists(self, session_id: str) -> bool:
        key = default_key_builder.build("session", session_id)
        return await redis_manager.client.exists(key) > 0

    async def refresh_session(self, session_id: str) -> None:
        key = default_key_builder.build("session", session_id)
        await redis_manager.client.expire(key, self._default_ttl)

    async def delete_session(self, session_id: str) -> None:
        key = default_key_builder.build("session", session_id)
        await redis_manager.client.delete(key)

    async def rotate_session(self, old_session_id: str) -> str:
        await self.delete_session(old_session_id)
        return await self.create_session()

    async def get_session_ttl(self, session_id: str) -> int:
        key = default_key_builder.build("session", session_id)
        return await redis_manager.client.ttl(key)


class AnonymousSessionStore:
    def __init__(self, default_ttl: int = 86400) -> None:
        self._manager = SessionManager(default_ttl)

    async def create_anonymous_session(self) -> str:
        return await self._manager.create_session()

    async def get_or_create_anonymous(self, session_id: str | None = None) -> str:
        return await self._manager.get_or_create(session_id)

    async def merge_to_authenticated(self, anonymous_id: str, authenticated_id: str) -> None:
        await self._manager.delete_session(anonymous_id)
        await self._manager.refresh_session(authenticated_id)
