from typing import Optional

from domain.models.conversation import ConversationState
from infrastructure.cache.redis_client import CacheService


class ShortTermMemory:
    def __init__(self, cache: CacheService):
        self.cache = cache
        self.ttl = 86400

    def _conversation_key(self, conversation_id: str) -> str:
        return f"conversation:{conversation_id}"

    def _session_key(self, user_id: str) -> str:
        return f"session:{user_id}"

    async def save_conversation_state(self, state: ConversationState) -> None:
        key = self._conversation_key(state.conversation_id)
        await self.cache.set(key, state.model_dump(), ttl=self.ttl)

    async def get_conversation_state(self, conversation_id: str) -> Optional[ConversationState]:
        key = self._conversation_key(conversation_id)
        data = await self.cache.get(key)
        if data:
            return ConversationState(**data)
        return None

    async def delete_conversation_state(self, conversation_id: str) -> None:
        key = self._conversation_key(conversation_id)
        await self.cache.delete(key)

    async def save_session_data(self, user_id: str, data: dict) -> None:
        key = self._session_key(user_id)
        await self.cache.set(key, data, ttl=self.ttl)

    async def get_session_data(self, user_id: str) -> Optional[dict]:
        key = self._session_key(user_id)
        return await self.cache.get(key)

    async def acquire_workflow_lock(self, conversation_id: str, ttl: int = 30) -> bool:
        lock_key = f"lock:workflow:{conversation_id}"
        return await self.cache.acquire_lock(lock_key, ttl)

    async def release_workflow_lock(self, conversation_id: str) -> None:
        lock_key = f"lock:workflow:{conversation_id}"
        await self.cache.release_lock(lock_key)
