from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.memory.events import (
    MemoryConfidenceChanged,
    MemoryCreated,
    MemoryDeleted,
    MemoryEvent,
    MemoryExpired,
    MemoryImportanceChanged,
    MemoryMerged,
    MemoryUpdated,
)
from domain.memory.policies import MemoryPolicies, default_policies
from domain.memory.state import IllegalMemoryTransitionError, MemoryStateMachine, MemoryStatus
from domain.memory.value_objects import (
    MemoryCategory,
    MemoryConfidence,
    MemoryId,
    MemoryImportance,
    MemoryKey,
    MemoryPriority,
    MemoryScope,
    MemorySource,
)


@dataclass
class MemoryRecord:
    memory_id: MemoryId = field(default_factory=MemoryId)
    key: MemoryKey | None = None
    value: str = ""
    memory_type: str = "fact"
    category: MemoryCategory = MemoryCategory.FACT
    scope: MemoryScope = MemoryScope.USER
    priority: MemoryPriority = MemoryPriority.MEDIUM
    confidence: MemoryConfidence = MemoryConfidence.MEDIUM
    importance: MemoryImportance = MemoryImportance.MEDIUM
    source: MemorySource = MemorySource.SYSTEM
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    version: int = 1

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1


@dataclass
class Memory:
    memory_id: MemoryId = field(default_factory=MemoryId)
    user_id: str = ""
    conversation_id: str | None = None
    session_id: str | None = None
    key: MemoryKey | None = None
    value: str = ""
    memory_type: str = "fact"
    category: MemoryCategory = MemoryCategory.FACT
    scope: MemoryScope = MemoryScope.USER
    priority: MemoryPriority = MemoryPriority.MEDIUM
    confidence: MemoryConfidence = MemoryConfidence.MEDIUM
    importance: MemoryImportance = MemoryImportance.MEDIUM
    source: MemorySource = MemorySource.SYSTEM
    state_machine: MemoryStateMachine = field(default_factory=MemoryStateMachine)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    records: list[MemoryRecord] = field(default_factory=list)
    policies: MemoryPolicies = field(default_factory=lambda: default_policies)
    events: list[MemoryEvent] = field(default_factory=list)
    correlation_id: str | None = None
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    @property
    def status(self) -> MemoryStatus:
        return self.state_machine.current_state

    @property
    def record_count(self) -> int:
        return len(self.records)

    @property
    def latest_record(self) -> MemoryRecord | None:
        if not self.records:
            return None
        return self.records[-1]

    @property
    def is_active(self) -> bool:
        return self.state_machine.is_active()

    @property
    def is_terminal(self) -> bool:
        return self.state_machine.is_terminal()

    @property
    def can_modify(self) -> bool:
        return self.state_machine.can_modify()

    def _record_event(self, event: MemoryEvent) -> None:
        event.memory_id = str(self.memory_id)
        event.correlation_id = self.correlation_id or ""
        self.events.append(event)

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1

    def activate(self) -> None:
        if self.state_machine.current_state == MemoryStatus.CREATED:
            event = self.state_machine.transition_to(MemoryStatus.ACTIVE)
            if event:
                self._record_event(event)
            self._record_event(
                MemoryCreated(
                    memory_id=str(self.memory_id),
                    user_id=self.user_id,
                    category=self.category.value,
                    scope=self.scope.value,
                    key=str(self.key) if self.key else "",
                )
            )
        self._touch()

    def update_value(self, new_value: str, new_confidence: MemoryConfidence | None = None) -> None:
        if not self.can_modify:
            raise IllegalMemoryTransitionError(
                from_state=self.status,
                to_state=MemoryStatus.UPDATED,
            )

        previous_value = self.value
        self.value = new_value

        if self.state_machine.can_transition_to(MemoryStatus.UPDATED):
            event = self.state_machine.transition_to(MemoryStatus.UPDATED)
            if event:
                self._record_event(event)
            self._record_event(
                MemoryUpdated(
                    memory_id=str(self.memory_id),
                    previous_value=previous_value,
                    new_value=new_value,
                )
            )
        self._touch()

        if new_confidence is not None and new_confidence != self.confidence:
            self._record_event(
                MemoryConfidenceChanged(
                    memory_id=str(self.memory_id),
                    previous_confidence=self.confidence.value,
                    new_confidence=new_confidence.value,
                )
            )
            self.confidence = new_confidence

    def merge(self, other: Memory) -> None:
        if not self.can_modify:
            raise IllegalMemoryTransitionError(
                from_state=self.status,
                to_state=MemoryStatus.MERGED,
            )
        if other.memory_id == self.memory_id:
            raise MemoryConflictError("Cannot merge memory with itself")

        for record in other.records:
            if record not in self.records:
                self.records.append(record)
        if other.value not in self.value:
            self.value = f"{self.value}; {other.value}"

        event = self.state_machine.transition_to(MemoryStatus.MERGED)
        if event:
            self._record_event(event)
        self._record_event(
            MemoryMerged(
                memory_id=str(self.memory_id),
                source_memory_ids=[str(other.memory_id)],
            )
        )
        self._touch()

    def archive(self, reason: str = "") -> None:
        if not self.state_machine.can_transition_to(MemoryStatus.ARCHIVED):
            raise IllegalMemoryTransitionError(
                from_state=self.status,
                to_state=MemoryStatus.ARCHIVED,
            )
        event = self.state_machine.transition_to(MemoryStatus.ARCHIVED)
        if event:
            self._record_event(event)
        self._touch()

    def restore(self) -> None:
        if not self.state_machine.can_transition_to(MemoryStatus.ACTIVE):
            raise IllegalMemoryTransitionError(
                from_state=self.status,
                to_state=MemoryStatus.ACTIVE,
            )
        event = self.state_machine.transition_to(MemoryStatus.ACTIVE)
        if event:
            self._record_event(event)
        self._touch()

    def expire(self, reason: str = "retention_reached") -> None:
        event = self.state_machine.transition_to(MemoryStatus.EXPIRED)
        if event:
            self._record_event(event)
        self._record_event(
            MemoryExpired(
                memory_id=str(self.memory_id),
                reason=reason,
            )
        )
        self._touch()

    def delete(self, reason: str = "") -> None:
        if not self.state_machine.can_transition_to(MemoryStatus.DELETED):
            raise IllegalMemoryTransitionError(
                from_state=self.status,
                to_state=MemoryStatus.DELETED,
            )
        event = self.state_machine.transition_to(MemoryStatus.DELETED)
        if event:
            self._record_event(event)
        self._record_event(
            MemoryDeleted(
                memory_id=str(self.memory_id),
                reason=reason,
            )
        )
        self._touch()

    def change_confidence(self, new_confidence: MemoryConfidence) -> None:
        if not self.can_modify:
            raise IllegalMemoryTransitionError(
                from_state=self.status,
                to_state=self.status,
            )
        previous = self.confidence
        self.confidence = new_confidence
        self._record_event(
            MemoryConfidenceChanged(
                memory_id=str(self.memory_id),
                previous_confidence=previous.value,
                new_confidence=new_confidence.value,
            )
        )
        self._touch()

    def change_importance(self, new_importance: MemoryImportance) -> None:
        if not self.can_modify:
            raise IllegalMemoryTransitionError(
                from_state=self.status,
                to_state=self.status,
            )
        previous = self.importance
        self.importance = new_importance
        self._record_event(
            MemoryImportanceChanged(
                memory_id=str(self.memory_id),
                previous_importance=previous.value,
                new_importance=new_importance.value,
            )
        )
        self._touch()

    def add_record(self, record: MemoryRecord) -> None:
        if not self.can_modify:
            raise IllegalMemoryTransitionError(
                from_state=self.status,
                to_state=self.status,
            )
        self.records.append(record)
        self._touch()

    def drain_events(self) -> list[MemoryEvent]:
        events = list(self.events)
        self.events.clear()
        return events

    def elapsed_since_created(self) -> float:
        delta = datetime.now(timezone.utc) - self.created_at
        return delta.total_seconds() / 86400.0

    def elapsed_since_updated(self) -> float:
        delta = datetime.now(timezone.utc) - self.updated_at
        return delta.total_seconds() / 86400.0


class MemoryConflictError(Exception):
    pass
