from unittest.mock import AsyncMock

import pytest

from application.memory.commands import (
    ArchiveMemoryCommand,
    ChangeConfidenceCommand,
    ChangeImportanceCommand,
    CreateMemoryCommand,
    DeleteMemoryCommand,
    MergeMemoryCommand,
    RestoreMemoryCommand,
    UpdateMemoryCommand,
)
from application.memory.queries import GetMemoryQuery, GetUserMemoriesQuery
from application.memory.service import MemoryApplicationService
from domain.memory.aggregate import Memory
from domain.memory.factory import MemoryFactory
from domain.memory.state import MemoryStatus
from domain.memory.value_objects import (
    MemoryCategory,
    MemoryConfidence,
    MemoryImportance,
    MemoryScope,
)


class TestMemoryApplicationService:
    def setup_method(self) -> None:
        self.repository = AsyncMock()
        self.service = MemoryApplicationService(
            repository=self.repository,
            factory=MemoryFactory(),
        )

    async def test_create_memory(self):
        self.repository.save = AsyncMock()
        self.repository.count_by_user = AsyncMock(return_value=0)
        command = CreateMemoryCommand(
            user_id="user-1",
            value="User prefers dark mode",
            category=MemoryCategory.PREFERENCE,
            scope=MemoryScope.USER,
        )
        memory = await self.service.create_memory(command)
        assert memory.user_id == "user-1"
        assert memory.value == "User prefers dark mode"
        assert memory.status == MemoryStatus.ACTIVE
        self.repository.save.assert_awaited()

    async def test_create_memory_with_conversation(self):
        self.repository.save = AsyncMock()
        self.repository.count_by_user = AsyncMock(return_value=0)
        command = CreateMemoryCommand(
            user_id="user-1",
            value="test",
            conversation_id="conv-1",
        )
        memory = await self.service.create_memory(command)
        assert memory.conversation_id == "conv-1"

    async def test_create_memory_exceeds_limit(self):
        self.repository.count_by_user = AsyncMock(return_value=1000)
        command = CreateMemoryCommand(
            user_id="user-1",
            value="test",
            scope=MemoryScope.USER,
        )
        from domain.memory.validator import MemoryValidationError
        with pytest.raises(MemoryValidationError):
            await self.service.create_memory(command)

    async def test_update_memory(self):
        memory = Memory(user_id="user-1", value="old")
        memory.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=memory)
        self.repository.save = AsyncMock()

        command = UpdateMemoryCommand(memory_id=str(memory.memory_id), value="new")
        result = await self.service.update_memory(command)
        assert result.value == "new"

    async def test_merge_memories(self):
        target = Memory(user_id="user-1", value="target")
        target.activate()
        source = Memory(user_id="user-1", value="source")
        source.activate()

        self.repository.get_by_id_str = AsyncMock(side_effect=[target, source])
        self.repository.save = AsyncMock()

        command = MergeMemoryCommand(
            target_memory_id=str(target.memory_id),
            source_memory_id=str(source.memory_id),
        )
        result = await self.service.merge_memories(command)
        assert "source" in result.value

    async def test_archive_memory(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=memory)
        self.repository.save = AsyncMock()

        command = ArchiveMemoryCommand(memory_id=str(memory.memory_id), reason="test")
        result = await self.service.archive_memory(command)
        assert result.status == MemoryStatus.ARCHIVED

    async def test_restore_memory(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        memory.archive()
        self.repository.get_by_id_str = AsyncMock(return_value=memory)
        self.repository.save = AsyncMock()

        command = RestoreMemoryCommand(memory_id=str(memory.memory_id))
        result = await self.service.restore_memory(command)
        assert result.status == MemoryStatus.ACTIVE

    async def test_delete_memory(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=memory)
        self.repository.save = AsyncMock()

        command = DeleteMemoryCommand(memory_id=str(memory.memory_id), reason="test")
        result = await self.service.delete_memory(command)
        assert result.status == MemoryStatus.DELETED

    async def test_change_confidence(self):
        memory = Memory(user_id="user-1", value="test", confidence=MemoryConfidence.LOW)
        memory.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=memory)
        self.repository.save = AsyncMock()

        command = ChangeConfidenceCommand(
            memory_id=str(memory.memory_id),
            new_confidence=MemoryConfidence.HIGH,
        )
        result = await self.service.change_confidence(command)
        assert result.confidence == MemoryConfidence.HIGH

    async def test_change_importance(self):
        memory = Memory(user_id="user-1", value="test", importance=MemoryImportance.LOW)
        memory.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=memory)
        self.repository.save = AsyncMock()

        command = ChangeImportanceCommand(
            memory_id=str(memory.memory_id),
            new_importance=MemoryImportance.HIGH,
        )
        result = await self.service.change_importance(command)
        assert result.importance == MemoryImportance.HIGH

    async def test_get_memory(self):
        memory = Memory(user_id="user-1", value="test")
        self.repository.get_by_id_str = AsyncMock(return_value=memory)
        query = GetMemoryQuery(memory_id=str(memory.memory_id))
        result = await self.service.get_memory(query)
        assert result is not None
        assert result.user_id == "user-1"

    async def test_get_memory_not_found(self):
        self.repository.get_by_id_str = AsyncMock(return_value=None)
        query = GetMemoryQuery(memory_id="nonexistent")
        result = await self.service.get_memory(query)
        assert result is None

    async def test_get_user_memories(self):
        self.repository.get_by_user = AsyncMock(return_value=[])
        query = GetUserMemoriesQuery(user_id="user-1")
        result = await self.service.get_user_memories(query)
        assert len(result) == 0

    async def test_get_memory_summary(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=memory)
        summary = await self.service.get_memory_summary(str(memory.memory_id))
        assert summary is not None
        assert summary["category"] == "fact"
        assert summary["status"] == "active"

    async def test_get_memory_summary_not_found(self):
        self.repository.get_by_id_str = AsyncMock(return_value=None)
        summary = await self.service.get_memory_summary("nonexistent")
        assert summary is None

    async def test_process_expirations(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        self.repository.expire_old = AsyncMock(return_value=[memory])
        self.repository.save = AsyncMock()

        expired = await self.service.process_expirations()
        assert len(expired) == 1
        assert expired[0].status == MemoryStatus.EXPIRED
