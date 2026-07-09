import pytest

from domain.memory.factory import MemoryFactory
from domain.memory.state import MemoryStatus
from domain.memory.validator import MemoryValidationError
from domain.memory.value_objects import (
    MemoryCategory,
    MemoryConfidence,
    MemoryImportance,
    MemoryKey,
    MemoryPriority,
    MemoryScope,
    MemorySource,
)


class TestMemoryFactory:
    def setup_method(self) -> None:
        self.factory = MemoryFactory()

    def test_create_memory(self):
        memory = self.factory.create(
            user_id="user-1",
            value="User prefers dark mode",
            category=MemoryCategory.PREFERENCE,
            scope=MemoryScope.USER,
        )
        assert memory.user_id == "user-1"
        assert memory.value == "User prefers dark mode"
        assert memory.category == MemoryCategory.PREFERENCE
        assert memory.scope == MemoryScope.USER
        assert memory.status == MemoryStatus.ACTIVE
        assert memory.version >= 1

    def test_create_memory_with_key(self):
        key = MemoryKey(namespace="preferences", key="theme")
        memory = self.factory.create(
            user_id="user-1",
            value="dark",
            key=key,
        )
        assert memory.key is not None
        assert str(memory.key) == "preferences:theme"

    def test_create_memory_with_conversation(self):
        memory = self.factory.create(
            user_id="user-1",
            value="Discussed project timeline",
            category=MemoryCategory.CONVERSATION,
            scope=MemoryScope.CONVERSATION,
            conversation_id="conv-1",
        )
        assert memory.conversation_id == "conv-1"
        assert memory.scope == MemoryScope.CONVERSATION

    def test_create_memory_with_tags(self):
        memory = self.factory.create(
            user_id="user-1",
            value="test",
            tags=["important", "follow-up"],
        )
        assert "important" in memory.tags

    def test_create_memory_all_fields(self):
        memory = self.factory.create(
            user_id="user-1",
            value="test",
            category=MemoryCategory.FACT,
            scope=MemoryScope.USER,
            memory_type="long_term",
            priority=MemoryPriority.HIGH,
            confidence=MemoryConfidence.CERTAIN,
            importance=MemoryImportance.CRITICAL,
            source=MemorySource.USER_INPUT,
            correlation_id="corr-1",
        )
        assert memory.memory_type == "long_term"
        assert memory.priority == MemoryPriority.HIGH
        assert memory.confidence == MemoryConfidence.CERTAIN
        assert memory.importance == MemoryImportance.CRITICAL
        assert memory.source == MemorySource.USER_INPUT
        assert memory.correlation_id == "corr-1"

    def test_create_memory_empty_user_id_raises(self):
        with pytest.raises(MemoryValidationError):
            self.factory.create(user_id="", value="test")

    def test_create_memory_empty_value_raises(self):
        with pytest.raises(MemoryValidationError):
            self.factory.create(user_id="user-1", value="")

    def test_create_memory_emits_events(self):
        memory = self.factory.create(user_id="user-1", value="test")
        events = memory.drain_events()
        event_types = [type(e).__name__ for e in events]
        assert "MemoryCreated" in event_types

    def test_create_memory_with_metadata(self):
        memory = self.factory.create(
            user_id="user-1",
            value="test",
            metadata={"source_url": "https://example.com"},
        )
        assert memory.metadata["source_url"] == "https://example.com"
