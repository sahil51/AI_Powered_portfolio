from __future__ import annotations

from domain.knowledge.events import (
    KnowledgeActivated,
    KnowledgeArchived,
    KnowledgeChunked,
    KnowledgeDeleted,
    KnowledgeEmbedded,
    KnowledgeEvent,
    KnowledgeIndexed,
    KnowledgeProcessingStarted,
    KnowledgeUploaded,
)
from domain.knowledge.value_objects import KnowledgeStatus

STATE_TRANSITIONS: dict[KnowledgeStatus, set[KnowledgeStatus]] = {
    KnowledgeStatus.CREATED: {
        KnowledgeStatus.UPLOADED,
        KnowledgeStatus.ARCHIVED,
        KnowledgeStatus.DELETED,
    },
    KnowledgeStatus.UPLOADED: {
        KnowledgeStatus.PROCESSING,
        KnowledgeStatus.ARCHIVED,
        KnowledgeStatus.DELETED,
    },
    KnowledgeStatus.PROCESSING: {
        KnowledgeStatus.CHUNKED,
        KnowledgeStatus.DELETED,
    },
    KnowledgeStatus.CHUNKED: {
        KnowledgeStatus.EMBEDDED,
        KnowledgeStatus.PROCESSING,
        KnowledgeStatus.DELETED,
    },
    KnowledgeStatus.EMBEDDED: {
        KnowledgeStatus.INDEXED,
        KnowledgeStatus.CHUNKED,
        KnowledgeStatus.DELETED,
    },
    KnowledgeStatus.INDEXED: {
        KnowledgeStatus.ACTIVE,
        KnowledgeStatus.EMBEDDED,
        KnowledgeStatus.DELETED,
    },
    KnowledgeStatus.ACTIVE: {
        KnowledgeStatus.ARCHIVED,
        KnowledgeStatus.INDEXED,
    },
    KnowledgeStatus.ARCHIVED: {
        KnowledgeStatus.DELETED,
        KnowledgeStatus.ACTIVE,
    },
    KnowledgeStatus.DELETED: set(),
}

EVENT_MAP: dict[tuple[KnowledgeStatus, KnowledgeStatus], type[KnowledgeEvent]] = {
    (KnowledgeStatus.CREATED, KnowledgeStatus.UPLOADED): KnowledgeUploaded,
    (KnowledgeStatus.CREATED, KnowledgeStatus.ARCHIVED): KnowledgeArchived,
    (KnowledgeStatus.CREATED, KnowledgeStatus.DELETED): KnowledgeDeleted,
    (KnowledgeStatus.UPLOADED, KnowledgeStatus.PROCESSING): KnowledgeProcessingStarted,
    (KnowledgeStatus.UPLOADED, KnowledgeStatus.ARCHIVED): KnowledgeArchived,
    (KnowledgeStatus.UPLOADED, KnowledgeStatus.DELETED): KnowledgeDeleted,
    (KnowledgeStatus.PROCESSING, KnowledgeStatus.CHUNKED): KnowledgeChunked,
    (KnowledgeStatus.PROCESSING, KnowledgeStatus.DELETED): KnowledgeDeleted,
    (KnowledgeStatus.CHUNKED, KnowledgeStatus.EMBEDDED): KnowledgeEmbedded,
    (KnowledgeStatus.CHUNKED, KnowledgeStatus.PROCESSING): KnowledgeProcessingStarted,
    (KnowledgeStatus.CHUNKED, KnowledgeStatus.DELETED): KnowledgeDeleted,
    (KnowledgeStatus.EMBEDDED, KnowledgeStatus.INDEXED): KnowledgeIndexed,
    (KnowledgeStatus.EMBEDDED, KnowledgeStatus.CHUNKED): KnowledgeChunked,
    (KnowledgeStatus.EMBEDDED, KnowledgeStatus.DELETED): KnowledgeDeleted,
    (KnowledgeStatus.INDEXED, KnowledgeStatus.ACTIVE): KnowledgeActivated,
    (KnowledgeStatus.INDEXED, KnowledgeStatus.EMBEDDED): KnowledgeEmbedded,
    (KnowledgeStatus.INDEXED, KnowledgeStatus.DELETED): KnowledgeDeleted,
    (KnowledgeStatus.ACTIVE, KnowledgeStatus.ARCHIVED): KnowledgeArchived,
    (KnowledgeStatus.ACTIVE, KnowledgeStatus.INDEXED): KnowledgeIndexed,
    (KnowledgeStatus.ARCHIVED, KnowledgeStatus.DELETED): KnowledgeDeleted,
    (KnowledgeStatus.ARCHIVED, KnowledgeStatus.ACTIVE): KnowledgeActivated,
}


class IllegalKnowledgeTransitionError(Exception):
    def __init__(self, from_state: KnowledgeStatus, to_state: KnowledgeStatus) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Illegal knowledge state transition: {from_state.value} -> {to_state.value}")


class KnowledgeStateMachine:
    def __init__(self, current_state: KnowledgeStatus = KnowledgeStatus.CREATED) -> None:
        self._current_state = current_state

    @property
    def current_state(self) -> KnowledgeStatus:
        return self._current_state

    def can_transition_to(self, target: KnowledgeStatus) -> bool:
        allowed = STATE_TRANSITIONS.get(self._current_state, set())
        return target in allowed

    def allowed_transitions(self) -> set[KnowledgeStatus]:
        return STATE_TRANSITIONS.get(self._current_state, set())

    def transition_to(self, target: KnowledgeStatus) -> KnowledgeEvent | None:
        if not self.can_transition_to(target):
            raise IllegalKnowledgeTransitionError(self._current_state, target)
        event_class = EVENT_MAP.get((self._current_state, target))
        self._current_state = target
        if event_class:
            return event_class()
        return None

    def is_terminal(self) -> bool:
        return self._current_state in (KnowledgeStatus.DELETED,)

    def is_active(self) -> bool:
        return self._current_state not in (
            KnowledgeStatus.ARCHIVED,
            KnowledgeStatus.DELETED,
        )

    def can_process(self) -> bool:
        return self._current_state in (
            KnowledgeStatus.UPLOADED,
            KnowledgeStatus.CHUNKED,
        )

    def can_embed(self) -> bool:
        return self._current_state == KnowledgeStatus.CHUNKED

    def can_index(self) -> bool:
        return self._current_state == KnowledgeStatus.EMBEDDED

    def can_activate(self) -> bool:
        return self._current_state == KnowledgeStatus.INDEXED
