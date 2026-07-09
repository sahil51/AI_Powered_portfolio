import json
from hashlib import sha256

from application.memory.retrieval import MemoryFilter, MemoryPage, MemoryResult, MemorySort
from domain.memory.aggregate import Memory
from infrastructure.cache.connection import redis_manager
from infrastructure.cache.key_builder import default_key_builder


class MemoryCacheService:
    def __init__(self, default_ttl: int = 300) -> None:
        self._default_ttl = default_ttl

    def build_search_key(
        self,
        user_id: str,
        filter_obj: MemoryFilter | None = None,
        sort: MemorySort | None = None,
        page: MemoryPage | None = None,
    ) -> str:
        raw = f"search:{user_id}"
        if filter_obj:
            raw += f":f={json.dumps(filter_obj.to_repo_kwargs(), sort_keys=True, default=str)}"
        if sort:
            raw += f":s={sort.sort_by}:{sort.sort_desc}"
        if page:
            raw += f":p={page.skip}:{page.limit}"
        return default_key_builder.build("memory", sha256(raw.encode()).hexdigest()[:32])

    def build_memory_key(self, memory_id: str) -> str:
        return default_key_builder.build("memory", memory_id)

    def build_user_key(self, user_id: str) -> str:
        return default_key_builder.build("memory_user", user_id)

    async def get_result(self, key: str) -> MemoryResult | None:
        try:
            data = await redis_manager.client.get(key)
        except RuntimeError:
            return None
        if data is None:
            return None
        return MemoryResult(**json.loads(data))

    async def set_result(self, key: str, result: MemoryResult) -> None:
        try:
            data = json.dumps(result.to_dict(), default=str)
            await redis_manager.client.setex(key, self._default_ttl, data)
        except RuntimeError:
            pass

    async def get_memory_metadata(self, memory_id: str) -> Memory | None:
        key = self.build_memory_key(memory_id)
        try:
            data = await redis_manager.client.get(key)
        except RuntimeError:
            return None
        if data is None:
            return None
        return Memory(**json.loads(data))

    async def set_memory_metadata(self, memory: Memory) -> None:
        try:
            key = self.build_memory_key(str(memory.memory_id))
            data = json.dumps({
                "memory_id": str(memory.memory_id),
                "user_id": memory.user_id,
                "category": memory.category.value,
                "scope": memory.scope.value,
                "status": memory.status.value,
                "priority": memory.priority.value,
                "confidence": memory.confidence.value,
                "importance": memory.importance.value,
                "tags": memory.tags,
                "version": memory.version,
            }, default=str)
            await redis_manager.client.setex(key, self._default_ttl, data)
        except RuntimeError:
            pass

    async def invalidate_memory(self, memory_id: str) -> None:
        key = self.build_memory_key(memory_id)
        try:
            await redis_manager.client.delete(key)
        except RuntimeError:
            pass

    async def invalidate_user_memories(self, user_id: str) -> None:
        key = self.build_user_key(user_id)
        try:
            await redis_manager.client.delete(key)
        except RuntimeError:
            pass
