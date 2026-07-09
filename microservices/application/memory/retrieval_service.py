from collections.abc import Sequence

from application.memory.cache import MemoryCacheService
from application.memory.retrieval import (
    MemoryFilter,
    MemoryPage,
    MemoryQueryEngine,
    MemoryRankingEngine,
    MemoryResult,
    MemorySelectionEngine,
    MemorySort,
)
from domain.memory.aggregate import Memory
from domain.memory.repository import MemoryRepository
from domain.memory.value_objects import MemoryCategory, MemoryScope


class MemorySearchService:
    def __init__(
        self,
        repository: MemoryRepository,
        query_engine: MemoryQueryEngine | None = None,
        cache: MemoryCacheService | None = None,
    ) -> None:
        self._repository = repository
        self._query_engine = query_engine or MemoryQueryEngine()
        self._cache = cache or MemoryCacheService()

    async def search(
        self,
        user_id: str,
        filter_obj: MemoryFilter | None = None,
        sort: MemorySort | None = None,
        page: MemoryPage | None = None,
    ) -> MemoryResult:
        cache_key = self._cache.build_search_key(user_id, filter_obj, sort, page)
        cached = await self._cache.get_result(cache_key)
        if cached is not None:
            return cached

        if filter_obj is None:
            filter_obj = MemoryFilter()
        filter_obj.user_id = user_id

        kwargs = filter_obj.to_repo_kwargs()
        kwargs["skip"] = page.skip if page else 0
        kwargs["limit"] = page.limit if page else 20
        if sort:
            kwargs["sort_by"] = sort.sort_by
            kwargs["sort_desc"] = sort.sort_desc

        memories, total = await self._repository.search_advanced(**kwargs)
        result = MemoryResult(items=list(memories), total=total, skip=kwargs["skip"], limit=kwargs["limit"])

        await self._cache.set_result(cache_key, result)
        return result

    async def search_by_user(
        self,
        user_id: str,
        category: MemoryCategory | None = None,
        scope: MemoryScope | None = None,
        limit: int = 50,
    ) -> Sequence[Memory]:
        return await self._repository.get_by_user(user_id, category, scope, limit)

    async def search_by_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> Sequence[Memory]:
        return await self._repository.get_by_conversation(conversation_id, limit)


class MemoryRetrievalService:
    def __init__(
        self,
        repository: MemoryRepository,
        search_service: MemorySearchService | None = None,
        query_engine: MemoryQueryEngine | None = None,
        ranking_engine: MemoryRankingEngine | None = None,
        selection_engine: MemorySelectionEngine | None = None,
        cache: MemoryCacheService | None = None,
    ) -> None:
        self._repository = repository
        self._search = search_service or MemorySearchService(repository, query_engine, cache)
        self._query_engine = query_engine or MemoryQueryEngine()
        self._ranking_engine = ranking_engine or MemoryRankingEngine()
        self._selection_engine = selection_engine or MemorySelectionEngine()
        self._cache = cache or MemoryCacheService()

    async def get_memory(self, memory_id: str) -> Memory | None:
        cached = await self._cache.get_memory_metadata(memory_id)
        if cached is not None:
            return cached
        memory = await self._repository.get_by_id_str(memory_id)
        if memory:
            await self._cache.set_memory_metadata(memory)
        return memory

    async def search(
        self,
        user_id: str,
        filter_obj: MemoryFilter | None = None,
        sort: MemorySort | None = None,
        page: MemoryPage | None = None,
    ) -> MemoryResult:
        return await self._search.search(user_id, filter_obj, sort, page)

    async def get_user_memories(
        self,
        user_id: str,
        category: MemoryCategory | None = None,
        scope: MemoryScope | None = None,
        limit: int = 50,
    ) -> Sequence[Memory]:
        return await self._repository.get_by_user(user_id, category, scope, limit)

    async def get_conversation_memories(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> Sequence[Memory]:
        return await self._repository.get_by_conversation(conversation_id, limit)

    async def get_memory_by_key(self, user_id: str, namespace: str, key: str) -> Memory | None:
        return await self._repository.get_by_key(user_id, namespace, key)

    async def rank_memories(
        self,
        memories: list[Memory],
        sort: MemorySort | None = None,
    ) -> list[Memory]:
        return self._ranking_engine.rank(memories, sort)

    async def select_top_memories(
        self,
        memories: list[Memory],
        count: int,
        sort: MemorySort | None = None,
    ) -> list[Memory]:
        return self._selection_engine.select_top(memories, count, sort)

    async def invalidate_cache(self, memory_id: str) -> None:
        await self._cache.invalidate_memory(memory_id)
