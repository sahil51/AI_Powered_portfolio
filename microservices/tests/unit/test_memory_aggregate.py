import pytest

from domain.memory.aggregate import Memory, MemoryConflictError, MemoryRecord
from domain.memory.state import IllegalMemoryTransitionError, MemoryStateMachine, MemoryStatus
from domain.memory.value_objects import (
    MemoryConfidence,
    MemoryImportance,
)


class TestMemoryAggregate:
    def test_create_memory(self):
        memory = Memory(user_id="user-1", value="test value")
        assert memory.user_id == "user-1"
        assert memory.value == "test value"
        assert memory.status == MemoryStatus.CREATED
        assert memory.version == 1
        assert memory.record_count == 0

    def test_activate_memory(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        assert memory.status == MemoryStatus.ACTIVE
        assert memory.is_active
        assert memory.can_modify

    def test_update_value(self):
        memory = Memory(user_id="user-1", value="old")
        memory.activate()
        memory.update_value("new")
        assert memory.value == "new"
        assert memory.status == MemoryStatus.UPDATED

    def test_update_value_with_confidence(self):
        memory = Memory(user_id="user-1", value="old", confidence=MemoryConfidence.LOW)
        memory.activate()
        memory.update_value("new", MemoryConfidence.HIGH)
        assert memory.confidence == MemoryConfidence.HIGH
        events = memory.drain_events()
        event_types = [type(e).__name__ for e in events]
        assert "MemoryConfidenceChanged" in event_types

    def test_cannot_update_deleted(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        memory.delete()
        with pytest.raises(IllegalMemoryTransitionError):
            memory.update_value("new")

    def test_merge_memories(self):
        target = Memory(user_id="user-1", value="target")
        target.activate()
        source = Memory(user_id="user-1", value="source")
        source.activate()
        source_records = [MemoryRecord(value="record1"), MemoryRecord(value="record2")]
        for r in source_records:
            source.add_record(r)

        target.merge(source)
        assert target.status == MemoryStatus.MERGED
        assert "source" in target.value

    def test_merge_self_raises(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        with pytest.raises(MemoryConflictError):
            memory.merge(memory)

    def test_archive_and_restore(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        memory.archive(reason="no longer needed")
        assert memory.status == MemoryStatus.ARCHIVED

        memory.restore()
        assert memory.status == MemoryStatus.ACTIVE

    def test_expire_memory(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        memory.expire(reason="retention_reached")
        assert memory.status == MemoryStatus.EXPIRED

    def test_delete_memory(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        memory.delete(reason="user_requested")
        assert memory.status == MemoryStatus.DELETED
        assert memory.is_terminal

    def test_change_confidence(self):
        memory = Memory(user_id="user-1", value="test", confidence=MemoryConfidence.LOW)
        memory.activate()
        memory.change_confidence(MemoryConfidence.HIGH)
        assert memory.confidence == MemoryConfidence.HIGH
        events = memory.drain_events()
        assert any(type(e).__name__ == "MemoryConfidenceChanged" for e in events)

    def test_change_importance(self):
        memory = Memory(user_id="user-1", value="test", importance=MemoryImportance.LOW)
        memory.activate()
        memory.change_importance(MemoryImportance.HIGH)
        assert memory.importance == MemoryImportance.HIGH
        events = memory.drain_events()
        assert any(type(e).__name__ == "MemoryImportanceChanged" for e in events)

    def test_add_record(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        record = MemoryRecord(value="record data", tags=["tag1"])
        memory.add_record(record)
        assert memory.record_count == 1
        assert memory.records[0].value == "record data"

    def test_latest_record(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        assert memory.latest_record is None
        memory.add_record(MemoryRecord(value="first"))
        assert memory.latest_record is not None
        assert memory.latest_record.value == "first"

    def test_drain_events(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        events = memory.drain_events()
        assert len(events) >= 1
        assert memory.events == []

    def test_elapsed_since_created(self):
        memory = Memory(user_id="user-1", value="test")
        elapsed = memory.elapsed_since_created()
        assert elapsed >= 0

    def test_cannot_delete_from_created(self):
        memory = Memory(user_id="user-1", value="test")
        memory.delete()
        assert memory.status == MemoryStatus.DELETED

    def test_cannot_archive_from_created(self):
        memory = Memory(user_id="user-1", value="test")
        with pytest.raises(IllegalMemoryTransitionError):
            memory.archive()

    def test_cannot_restore_active(self):
        memory = Memory(user_id="user-1", value="test")
        memory.activate()
        with pytest.raises(IllegalMemoryTransitionError):
            memory.restore()

    def test_full_lifecycle(self):
        memory = Memory(user_id="user-1", value="start")
        memory.activate()
        memory.update_value("updated")
        memory.archive(reason="test")
        memory.restore()
        memory.update_value("final")
        memory.expire()
        memory.delete()
        assert memory.status == MemoryStatus.DELETED

    @staticmethod
    def _make_memory() -> Memory:
        return Memory(user_id="user-1", value="test")


class TestMemoryStateMachine:
    def test_initial_state(self):
        sm = MemoryStateMachine()
        assert sm.current_state == MemoryStatus.CREATED

    def test_transition_to_active(self):
        sm = MemoryStateMachine()
        sm.transition_to(MemoryStatus.ACTIVE)
        assert sm.current_state == MemoryStatus.ACTIVE

    def test_invalid_transition_raises(self):
        sm = MemoryStateMachine()
        with pytest.raises(IllegalMemoryTransitionError):
            sm.transition_to(MemoryStatus.ARCHIVED)

    def test_terminal_state(self):
        sm = MemoryStateMachine(MemoryStatus.DELETED)
        assert sm.is_terminal()
        sm2 = MemoryStateMachine(MemoryStatus.ACTIVE)
        assert not sm2.is_terminal()

    def test_is_active(self):
        assert MemoryStateMachine(MemoryStatus.ACTIVE).is_active()
        assert MemoryStateMachine(MemoryStatus.UPDATED).is_active()
        assert MemoryStateMachine(MemoryStatus.MERGED).is_active()
        assert not MemoryStateMachine(MemoryStatus.CREATED).is_active()
        assert not MemoryStateMachine(MemoryStatus.DELETED).is_active()

    def test_can_modify(self):
        assert MemoryStateMachine(MemoryStatus.CREATED).can_modify()
        assert MemoryStateMachine(MemoryStatus.ACTIVE).can_modify()
        assert not MemoryStateMachine(MemoryStatus.ARCHIVED).can_modify()
        assert not MemoryStateMachine(MemoryStatus.DELETED).can_modify()

    def test_full_lifecycle_transitions(self):
        sm = MemoryStateMachine()
        sm.transition_to(MemoryStatus.ACTIVE)
        sm.transition_to(MemoryStatus.UPDATED)
        sm.transition_to(MemoryStatus.MERGED)
        sm.transition_to(MemoryStatus.ARCHIVED)
        sm.transition_to(MemoryStatus.ACTIVE)
        sm.transition_to(MemoryStatus.EXPIRED)
        sm.transition_to(MemoryStatus.DELETED)
        assert sm.current_state == MemoryStatus.DELETED

    def test_allowed_transitions_from_active(self):
        sm = MemoryStateMachine(MemoryStatus.ACTIVE)
        allowed = sm.allowed_transitions()
        assert MemoryStatus.UPDATED in allowed
        assert MemoryStatus.MERGED in allowed
        assert MemoryStatus.EXPIRED in allowed
        assert MemoryStatus.ARCHIVED in allowed
        assert MemoryStatus.DELETED in allowed
        assert MemoryStatus.CREATED not in allowed

    def test_cannot_transition_from_deleted(self):
        sm = MemoryStateMachine(MemoryStatus.DELETED)
        allowed = sm.allowed_transitions()
        assert len(allowed) == 0
