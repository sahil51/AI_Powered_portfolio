from unittest.mock import AsyncMock

from application.memory.summary import MemorySummaryService
from domain.memory.aggregate import Memory
from domain.memory.value_objects import MemoryCategory, MemoryScope


class TestMemorySummaryService:
    def setup_method(self) -> None:
        self.repository = AsyncMock()
        self.service = MemorySummaryService(repository=self.repository)

    async def test_get_user_summary(self):
        memories = [
            Memory(user_id="u1", value="a", category=MemoryCategory.FACT, scope=MemoryScope.USER),
            Memory(user_id="u1", value="b", category=MemoryCategory.PREFERENCE, scope=MemoryScope.USER),
        ]
        for m in memories:
            m.activate()
        self.repository.search_advanced = AsyncMock(return_value=(memories, 2))
        summary = await self.service.get_user_summary("u1")
        assert summary.total_count == 2
        assert summary.active_count == 2
        assert "fact" in summary.by_category
        assert "preference" in summary.by_category

    async def test_get_conversation_summary(self):
        self.repository.search_advanced = AsyncMock(return_value=([], 0))
        summary = await self.service.get_conversation_summary("conv-1")
        assert summary.total_count == 0

    async def test_get_global_summary(self):
        self.repository.search_advanced = AsyncMock(return_value=([], 0))
        summary = await self.service.get_global_summary()
        assert summary.total_count == 0

    async def test_summary_with_tags(self):
        memories = [
            Memory(user_id="u1", value="a", tags=["important", "urgent"]),
            Memory(user_id="u1", value="b", tags=["important"]),
        ]
        for m in memories:
            m.activate()
        self.repository.search_advanced = AsyncMock(return_value=(memories, 2))
        summary = await self.service.get_user_summary("u1")
        assert len(summary.top_tags) > 0
        tag_dict = dict(summary.top_tags)
        assert tag_dict["important"] == 2

    async def test_get_memory_detail_summary(self):
        memory = Memory(user_id="u1", value="test")
        memory.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=memory)
        detail = await self.service.get_memory_detail_summary(str(memory.memory_id))
        assert detail is not None
        assert detail["category"] == "fact"
        assert detail["status"] == "active"

    async def test_get_memory_detail_summary_not_found(self):
        self.repository.get_by_id_str = AsyncMock(return_value=None)
        detail = await self.service.get_memory_detail_summary("nonexistent")
        assert detail is None
