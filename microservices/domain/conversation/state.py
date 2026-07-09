from __future__ import annotations

from enum import Enum

from domain.conversation.events import (
    ConversationActivated,
    ConversationArchived,
    ConversationCompleted,
    ConversationEvent,
    ConversationPaused,
    ConversationResumed,
)


class ConversationState(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    COLLECTING_INFORMATION = "collecting_information"
    WAITING_CONFIRMATION = "waiting_confirmation"
    WAITING_EXTERNAL_WORKFLOW = "waiting_external_workflow"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


STATE_TRANSITIONS: dict[ConversationState, set[ConversationState]] = {
    ConversationState.CREATED: {
        ConversationState.ACTIVE,
        ConversationState.CANCELLED,
        ConversationState.ARCHIVED,
    },
    ConversationState.ACTIVE: {
        ConversationState.COLLECTING_INFORMATION,
        ConversationState.WAITING_CONFIRMATION,
        ConversationState.WAITING_EXTERNAL_WORKFLOW,
        ConversationState.PAUSED,
        ConversationState.COMPLETED,
        ConversationState.CANCELLED,
    },
    ConversationState.COLLECTING_INFORMATION: {
        ConversationState.ACTIVE,
        ConversationState.WAITING_CONFIRMATION,
        ConversationState.WAITING_EXTERNAL_WORKFLOW,
        ConversationState.PAUSED,
        ConversationState.CANCELLED,
    },
    ConversationState.WAITING_CONFIRMATION: {
        ConversationState.ACTIVE,
        ConversationState.COLLECTING_INFORMATION,
        ConversationState.COMPLETED,
        ConversationState.CANCELLED,
    },
    ConversationState.WAITING_EXTERNAL_WORKFLOW: {
        ConversationState.ACTIVE,
        ConversationState.COLLECTING_INFORMATION,
        ConversationState.PAUSED,
        ConversationState.CANCELLED,
    },
    ConversationState.PAUSED: {
        ConversationState.RESUMED,
        ConversationState.CANCELLED,
        ConversationState.ARCHIVED,
    },
    ConversationState.RESUMED: {
        ConversationState.ACTIVE,
        ConversationState.COLLECTING_INFORMATION,
        ConversationState.WAITING_CONFIRMATION,
        ConversationState.WAITING_EXTERNAL_WORKFLOW,
        ConversationState.PAUSED,
        ConversationState.COMPLETED,
        ConversationState.CANCELLED,
    },
    ConversationState.COMPLETED: {
        ConversationState.ARCHIVED,
    },
    ConversationState.CANCELLED: {
        ConversationState.ARCHIVED,
    },
    ConversationState.ARCHIVED: set(),
}


EVENT_MAP: dict[tuple[ConversationState, ConversationState], type[ConversationEvent]] = {
    (ConversationState.CREATED, ConversationState.ACTIVE): ConversationActivated,
    (ConversationState.ACTIVE, ConversationState.PAUSED): ConversationPaused,
    (ConversationState.PAUSED, ConversationState.RESUMED): ConversationResumed,
    (ConversationState.ACTIVE, ConversationState.COMPLETED): ConversationCompleted,
    (ConversationState.CANCELLED, ConversationState.ARCHIVED): ConversationArchived,
    (ConversationState.COMPLETED, ConversationState.ARCHIVED): ConversationArchived,
}


class ConversationStateMachine:
    def __init__(self, current_state: ConversationState = ConversationState.CREATED) -> None:
        self._current_state = current_state

    @property
    def current_state(self) -> ConversationState:
        return self._current_state

    def can_transition_to(self, target: ConversationState) -> bool:
        return target in STATE_TRANSITIONS.get(self._current_state, set())

    def allowed_transitions(self) -> set[ConversationState]:
        return STATE_TRANSITIONS.get(self._current_state, set()).copy()

    def transition_to(self, target: ConversationState) -> ConversationEvent | None:
        if not self.can_transition_to(target):
            raise IllegalStateTransitionError(
                from_state=self._current_state,
                to_state=target,
            )
        event_type = EVENT_MAP.get((self._current_state, target))
        self._current_state = target
        if event_type is not None:
            return event_type()
        return None

    def is_terminal(self) -> bool:
        return self._current_state in (
            ConversationState.COMPLETED,
            ConversationState.CANCELLED,
            ConversationState.ARCHIVED,
        )

    def is_paused(self) -> bool:
        return self._current_state == ConversationState.PAUSED

    def can_accept_messages(self) -> bool:
        return self._current_state in (
            ConversationState.ACTIVE,
            ConversationState.COLLECTING_INFORMATION,
            ConversationState.WAITING_CONFIRMATION,
            ConversationState.WAITING_EXTERNAL_WORKFLOW,
            ConversationState.RESUMED,
        )


class IllegalStateTransitionError(Exception):
    def __init__(self, from_state: ConversationState, to_state: ConversationState) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Illegal state transition: {from_state.value} -> {to_state.value}")
