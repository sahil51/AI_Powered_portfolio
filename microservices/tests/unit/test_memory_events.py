
from domain.memory.events import (
    MemoryArchived,
    MemoryConfidenceChanged,
    MemoryCreated,
    MemoryDeleted,
    MemoryEvent,
    MemoryExpired,
    MemoryImportanceChanged,
    MemoryMerged,
    MemoryRestored,
    MemoryUpdated,
)


class TestMemoryEvents:
    def test_memory_created_event(self):
        event = MemoryCreated(memory_id="mem-1", user_id="user-1", category="fact", scope="user")
        assert event.memory_id == "mem-1"
        assert event.user_id == "user-1"
        assert event.category == "fact"
        assert isinstance(event, MemoryEvent)

    def test_memory_updated_event(self):
        event = MemoryUpdated(memory_id="mem-1", previous_value="old", new_value="new")
        assert event.previous_value == "old"
        assert event.new_value == "new"

    def test_memory_merged_event(self):
        event = MemoryMerged(memory_id="mem-1", source_memory_ids=["mem-2", "mem-3"])
        assert len(event.source_memory_ids) == 2
        assert "mem-2" in event.source_memory_ids

    def test_memory_archived_event(self):
        event = MemoryArchived(memory_id="mem-1", reason="archived")
        assert event.reason == "archived"

    def test_memory_expired_event(self):
        event = MemoryExpired(memory_id="mem-1")
        assert event.reason == "retention_reached"

    def test_memory_deleted_event(self):
        event = MemoryDeleted(memory_id="mem-1", reason="deleted")
        assert event.reason == "deleted"

    def test_memory_restored_event(self):
        event = MemoryRestored(memory_id="mem-1", reason="restored")
        assert event.reason == "restored"

    def test_confidence_changed_event(self):
        event = MemoryConfidenceChanged(
            memory_id="mem-1",
            previous_confidence="low",
            new_confidence="high",
        )
        assert event.previous_confidence == "low"
        assert event.new_confidence == "high"

    def test_importance_changed_event(self):
        event = MemoryImportanceChanged(
            memory_id="mem-1",
            previous_importance="low",
            new_importance="high",
        )
        assert event.previous_importance == "low"
        assert event.new_importance == "high"

    def test_event_has_timestamp(self):
        event = MemoryCreated(memory_id="mem-1", user_id="user-1", category="fact", scope="user")
        assert event.timestamp is not None

    def test_event_has_correlation_id(self):
        event = MemoryCreated(
            memory_id="mem-1", user_id="user-1",
            category="fact", scope="user", correlation_id="corr-1",
        )
        assert event.correlation_id == "corr-1"
