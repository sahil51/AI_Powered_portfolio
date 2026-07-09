from __future__ import annotations

from enum import Enum

from domain.memory.events import (
    MemoryArchived,
    MemoryDeleted,
    MemoryEvent,
    MemoryRestored,
)


class MemoryStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    UPDATED = "updated"
    MERGED = "merged"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DELETED = "deleted"


STATE_TRANSITIONS: dict[MemoryStatus, set[MemoryStatus]] = {
    MemoryStatus.CREATED: {MemoryStatus.ACTIVE, MemoryStatus.EXPIRED, MemoryStatus.DELETED},
    MemoryStatus.ACTIVE: {
        MemoryStatus.UPDATED, MemoryStatus.MERGED, MemoryStatus.EXPIRED,
        MemoryStatus.ARCHIVED, MemoryStatus.DELETED,
    },
    MemoryStatus.UPDATED: {
        MemoryStatus.ACTIVE, MemoryStatus.MERGED, MemoryStatus.EXPIRED,
        MemoryStatus.ARCHIVED, MemoryStatus.DELETED,
    },
    MemoryStatus.MERGED: {
        MemoryStatus.ACTIVE, MemoryStatus.ARCHIVED, MemoryStatus.DELETED,
    },
    MemoryStatus.EXPIRED: {
        MemoryStatus.ARCHIVED, MemoryStatus.DELETED,
    },
    MemoryStatus.ARCHIVED: {
        MemoryStatus.DELETED, MemoryStatus.ACTIVE,
    },
    MemoryStatus.DELETED: set(),
}


EVENT_MAP: dict[tuple[MemoryStatus, MemoryStatus], type[MemoryEvent]] = {
    (MemoryStatus.ARCHIVED, MemoryStatus.ACTIVE): MemoryRestored,
    (MemoryStatus.ACTIVE, MemoryStatus.ARCHIVED): MemoryArchived,
    (MemoryStatus.EXPIRED, MemoryStatus.ARCHIVED): MemoryArchived,
    (MemoryStatus.ACTIVE, MemoryStatus.DELETED): MemoryDeleted,
}


class MemoryStateMachine:
    def __init__(self, current_state: MemoryStatus = MemoryStatus.CREATED) -> None:
        self._current_state = current_state

    @property
    def current_state(self) -> MemoryStatus:
        return self._current_state

    def can_transition_to(self, target: MemoryStatus) -> bool:
        return target in STATE_TRANSITIONS.get(self._current_state, set())

    def allowed_transitions(self) -> set[MemoryStatus]:
        return STATE_TRANSITIONS.get(self._current_state, set()).copy()

    def transition_to(self, target: MemoryStatus) -> MemoryEvent | None:
        if not self.can_transition_to(target):
            raise IllegalMemoryTransitionError(
                from_state=self._current_state,
                to_state=target,
            )
        event_type = EVENT_MAP.get((self._current_state, target))
        self._current_state = target
        if event_type is not None:
            return event_type()
        return None

    def is_terminal(self) -> bool:
        return self._current_state == MemoryStatus.DELETED

    def is_active(self) -> bool:
        return self._current_state in (
            MemoryStatus.ACTIVE,
            MemoryStatus.UPDATED,
            MemoryStatus.MERGED,
        )

    def can_modify(self) -> bool:
        return self._current_state in (
            MemoryStatus.CREATED,
            MemoryStatus.ACTIVE,
            MemoryStatus.UPDATED,
            MemoryStatus.MERGED,
        )


class IllegalMemoryTransitionError(Exception):
    def __init__(self, from_state: MemoryStatus, to_state: MemoryStatus) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Illegal memory state transition: {from_state.value} -> {to_state.value}")
