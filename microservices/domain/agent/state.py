from domain.agent.events import (
    AgentArchived,
    AgentCancelled,
    AgentCompleted,
    AgentEvent,
    AgentFailed,
    AgentInitialized,
    AgentPaused,
    AgentRestarted,
    AgentResumed,
    AgentStarted,
)
from domain.agent.value_objects import AgentStatus

STATE_TRANSITIONS: dict[AgentStatus, set[AgentStatus]] = {
    AgentStatus.CREATED: {AgentStatus.INITIALIZED, AgentStatus.CANCELLED, AgentStatus.FAILED},
    AgentStatus.INITIALIZED: {AgentStatus.RUNNING, AgentStatus.CANCELLED, AgentStatus.FAILED},
    AgentStatus.RUNNING: {
        AgentStatus.WAITING, AgentStatus.PAUSED, AgentStatus.COMPLETED,
        AgentStatus.CANCELLED, AgentStatus.FAILED,
    },
    AgentStatus.WAITING: {AgentStatus.RUNNING, AgentStatus.CANCELLED, AgentStatus.FAILED},
    AgentStatus.PAUSED: {AgentStatus.RUNNING, AgentStatus.CANCELLED, AgentStatus.FAILED},
    AgentStatus.COMPLETED: {AgentStatus.ARCHIVED},
    AgentStatus.CANCELLED: {AgentStatus.ARCHIVED},
    AgentStatus.FAILED: {AgentStatus.ARCHIVED, AgentStatus.INITIALIZED},
    AgentStatus.ARCHIVED: set(),
}


EVENT_MAP: dict[tuple[AgentStatus, AgentStatus], type[AgentEvent]] = {
    (AgentStatus.CREATED, AgentStatus.INITIALIZED): AgentInitialized,
    (AgentStatus.INITIALIZED, AgentStatus.RUNNING): AgentStarted,
    (AgentStatus.RUNNING, AgentStatus.PAUSED): AgentPaused,
    (AgentStatus.PAUSED, AgentStatus.RUNNING): AgentResumed,
    (AgentStatus.RUNNING, AgentStatus.COMPLETED): AgentCompleted,
    (AgentStatus.RUNNING, AgentStatus.CANCELLED): AgentCancelled,
    (AgentStatus.RUNNING, AgentStatus.FAILED): AgentFailed,
    (AgentStatus.WAITING, AgentStatus.RUNNING): AgentResumed,
    (AgentStatus.COMPLETED, AgentStatus.ARCHIVED): AgentArchived,
    (AgentStatus.CANCELLED, AgentStatus.ARCHIVED): AgentArchived,
    (AgentStatus.FAILED, AgentStatus.ARCHIVED): AgentArchived,
    (AgentStatus.FAILED, AgentStatus.INITIALIZED): AgentRestarted,
}


class IllegalAgentTransitionError(Exception):
    def __init__(self, from_state: AgentStatus, to_state: AgentStatus) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Illegal agent state transition: {from_state.value} -> {to_state.value}")


class AgentStateMachine:
    def __init__(self, current_state: AgentStatus = AgentStatus.CREATED) -> None:
        self._current_state = current_state

    @property
    def current_state(self) -> AgentStatus:
        return self._current_state

    def can_transition_to(self, target: AgentStatus) -> bool:
        return target in STATE_TRANSITIONS.get(self._current_state, set())

    def allowed_transitions(self) -> set[AgentStatus]:
        return STATE_TRANSITIONS.get(self._current_state, set()).copy()

    def transition_to(self, target: AgentStatus) -> AgentEvent | None:
        if not self.can_transition_to(target):
            raise IllegalAgentTransitionError(
                from_state=self._current_state,
                to_state=target,
            )
        event_type = EVENT_MAP.get((self._current_state, target))
        self._current_state = target
        if event_type is not None:
            return event_type()
        return None

    def is_terminal(self) -> bool:
        return self._current_state in (AgentStatus.COMPLETED, AgentStatus.CANCELLED, AgentStatus.ARCHIVED)

    def is_active(self) -> bool:
        return self._current_state in (
            AgentStatus.RUNNING, AgentStatus.WAITING,
        )

    def can_execute(self) -> bool:
        return self._current_state in (
            AgentStatus.INITIALIZED, AgentStatus.RUNNING,
            AgentStatus.WAITING, AgentStatus.PAUSED,
        )

    def can_modify(self) -> bool:
        return self._current_state not in (
            AgentStatus.COMPLETED, AgentStatus.CANCELLED,
            AgentStatus.FAILED, AgentStatus.ARCHIVED,
        )


