from unittest.mock import AsyncMock

from application.memory.retrieval import MemoryFilter, MemoryPage
from application.memory.retrieval_service import MemoryRetrievalService, MemorySearchService
from domain.memory.aggregate import Memory
from domain.memory.value_objects import MemoryCategory, MemoryScope


class TestMemorySearchService:
    def setup_method(self) -> None:
        self.repository = AsyncMock()
        self.service = MemorySearchService(repository=self.repository)

    async def test_search(self):
        memory = Memory(user_id="u1", value="test")
        self.repository.search_advanced = AsyncMock(return_value=([memory], 1))

        result = await self.service.search(
            user_id="u1",
            filter_obj=MemoryFilter(),
            page=MemoryPage(skip=0, limit=20),
        )
        assert result.total == 1
        assert len(result.items) == 1

    async def test_search_by_user(self):
        self.repository.get_by_user = AsyncMock(return_value=[])
        result = await self.service.search_by_user("u1", MemoryCategory.FACT, MemoryScope.USER)
        assert len(result) == 0

    async def test_search_by_conversation(self):
        self.repository.get_by_conversation = AsyncMock(return_value=[])
        result = await self.service.search_by_conversation("conv-1")
        assert len(result) == 0


class TestMemoryRetrievalService:
    def setup_method(self) -> None:
        self.repository = AsyncMock()
        self.service = MemoryRetrievalService(repository=self.repository)

    async def test_get_memory(self):
        memory = Memory(user_id="u1", value="test")
        self.repository.get_by_id_str = AsyncMock(return_value=memory)
        result = await self.service.get_memory(str(memory.memory_id))
        assert result is not None
        assert result.user_id == "u1"

    async def test_get_memory_not_found(self):
        self.repository.get_by_id_str = AsyncMock(return_value=None)
        result = await self.service.get_memory("nonexistent")
        assert result is None

    async def test_get_user_memories(self):
        self.repository.get_by_user = AsyncMock(return_value=[])
        result = await self.service.get_user_memories("u1")
        assert len(result) == 0

    async def test_get_conversation_memories(self):
        self.repository.get_by_conversation = AsyncMock(return_value=[])
        result = await self.service.get_conversation_memories("conv-1")
        assert len(result) == 0

    async def test_get_memory_by_key(self):
        self.repository.get_by_key = AsyncMock(return_value=None)
        result = await self.service.get_memory_by_key("u1", "prefs", "theme")
        assert result is None

    async def test_rank_memories(self):
        m1 = Memory(user_id="u1", value="a")
        m2 = Memory(user_id="u1", value="b")
        m1.activate()
        m2.activate()
        ranked = await self.service.rank_memories([m1, m2])
        assert len(ranked) == 2

    async def test_select_top_memories(self):
        memories = [Memory(user_id="u1", value=f"t{i}") for i in range(5)]
        top = await self.service.select_top_memories(memories, 3)
        assert len(top) == 3
