from __future__ import annotations

from domain.meeting.events import (
    MeetingArchived,
    MeetingCollectingStarted,
    MeetingCompleted,
    MeetingConfirmed,
    MeetingEvent,
    MeetingFailed,
    MeetingReady,
    MeetingSubmitted,
    MeetingWaitingConfirmation,
)
from domain.meeting.value_objects import MeetingStatus

STATE_TRANSITIONS: dict[MeetingStatus, set[MeetingStatus]] = {
    MeetingStatus.CREATED: {
        MeetingStatus.COLLECTING_INFORMATION,
        MeetingStatus.CANCELLED,
        MeetingStatus.FAILED,
    },
    MeetingStatus.COLLECTING_INFORMATION: {
        MeetingStatus.WAITING_CONFIRMATION,
        MeetingStatus.READY,
        MeetingStatus.CANCELLED,
        MeetingStatus.FAILED,
    },
    MeetingStatus.WAITING_CONFIRMATION: {
        MeetingStatus.COLLECTING_INFORMATION,
        MeetingStatus.READY,
        MeetingStatus.CANCELLED,
        MeetingStatus.FAILED,
    },
    MeetingStatus.READY: {
        MeetingStatus.SUBMITTED,
        MeetingStatus.COLLECTING_INFORMATION,
        MeetingStatus.WAITING_CONFIRMATION,
        MeetingStatus.CANCELLED,
        MeetingStatus.FAILED,
    },
    MeetingStatus.SUBMITTED: {
        MeetingStatus.COMPLETED,
        MeetingStatus.FAILED,
    },
    MeetingStatus.COMPLETED: {
        MeetingStatus.ARCHIVED,
    },
    MeetingStatus.CANCELLED: {
        MeetingStatus.ARCHIVED,
    },
    MeetingStatus.FAILED: {
        MeetingStatus.ARCHIVED,
        MeetingStatus.COLLECTING_INFORMATION,
    },
    MeetingStatus.ARCHIVED: set(),
}

EVENT_MAP: dict[tuple[MeetingStatus, MeetingStatus], type[MeetingEvent]] = {
    (MeetingStatus.CREATED, MeetingStatus.COLLECTING_INFORMATION): MeetingCollectingStarted,
    (MeetingStatus.COLLECTING_INFORMATION, MeetingStatus.WAITING_CONFIRMATION): MeetingWaitingConfirmation,
    (MeetingStatus.COLLECTING_INFORMATION, MeetingStatus.READY): MeetingReady,
    (MeetingStatus.WAITING_CONFIRMATION, MeetingStatus.READY): MeetingConfirmed,
    (MeetingStatus.WAITING_CONFIRMATION, MeetingStatus.COLLECTING_INFORMATION): MeetingCollectingStarted,
    (MeetingStatus.READY, MeetingStatus.SUBMITTED): MeetingSubmitted,
    (MeetingStatus.READY, MeetingStatus.COLLECTING_INFORMATION): MeetingCollectingStarted,
    (MeetingStatus.READY, MeetingStatus.WAITING_CONFIRMATION): MeetingWaitingConfirmation,
    (MeetingStatus.SUBMITTED, MeetingStatus.COMPLETED): MeetingCompleted,
    (MeetingStatus.SUBMITTED, MeetingStatus.FAILED): MeetingFailed,
    (MeetingStatus.COMPLETED, MeetingStatus.ARCHIVED): MeetingArchived,
    (MeetingStatus.CANCELLED, MeetingStatus.ARCHIVED): MeetingArchived,
    (MeetingStatus.FAILED, MeetingStatus.ARCHIVED): MeetingArchived,
    (MeetingStatus.FAILED, MeetingStatus.COLLECTING_INFORMATION): MeetingCollectingStarted,
}


class IllegalMeetingTransitionError(Exception):
    def __init__(self, from_state: MeetingStatus, to_state: MeetingStatus) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Illegal meeting state transition: {from_state.value} -> {to_state.value}")


class MeetingStateMachine:
    def __init__(self, current_state: MeetingStatus = MeetingStatus.CREATED) -> None:
        self._current_state = current_state

    @property
    def current_state(self) -> MeetingStatus:
        return self._current_state

    def can_transition_to(self, target: MeetingStatus) -> bool:
        allowed = STATE_TRANSITIONS.get(self._current_state, set())
        return target in allowed

    def allowed_transitions(self) -> set[MeetingStatus]:
        return STATE_TRANSITIONS.get(self._current_state, set())

    def transition_to(self, target: MeetingStatus) -> MeetingEvent | None:
        if not self.can_transition_to(target):
            raise IllegalMeetingTransitionError(self._current_state, target)
        event_class = EVENT_MAP.get((self._current_state, target))
        self._current_state = target
        if event_class:
            return event_class()
        return None

    def is_terminal(self) -> bool:
        return self._current_state in (MeetingStatus.ARCHIVED,)

    def is_active(self) -> bool:
        return self._current_state not in (
            MeetingStatus.COMPLETED,
            MeetingStatus.CANCELLED,
            MeetingStatus.FAILED,
            MeetingStatus.ARCHIVED,
        )

    def can_collect(self) -> bool:
        return self._current_state in (
            MeetingStatus.CREATED,
            MeetingStatus.COLLECTING_INFORMATION,
        )

    def can_submit(self) -> bool:
        return self._current_state == MeetingStatus.READY
