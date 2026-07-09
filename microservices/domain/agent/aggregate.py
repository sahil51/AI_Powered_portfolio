from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.agent.events import (
    AgentArchived,
    AgentCancelled,
    AgentCompleted,
    AgentCreated,
    AgentEvent,
    AgentFailed,
    AgentHeartbeat,
    AgentPaused,
    AgentRestarted,
    AgentResumed,
    AgentStarted,
)
from domain.agent.policies import AgentPolicies, default_agent_policies
from domain.agent.state import AgentStateMachine, AgentStatus, IllegalAgentTransitionError
from domain.agent.value_objects import (
    AgentCapability,
    AgentHealthStatus,
    AgentId,
    AgentMetadata,
    AgentPriority,
    AgentType,
)


@dataclass
class Agent:
    agent_id: AgentId = field(default_factory=AgentId)
    name: str = ""
    agent_type: AgentType = AgentType.CUSTOM
    capabilities: set[AgentCapability] = field(default_factory=set)
    priority: AgentPriority = AgentPriority.MEDIUM
    metadata: AgentMetadata = field(default_factory=AgentMetadata)
    state_machine: AgentStateMachine = field(default_factory=AgentStateMachine)
    health_status: AgentHealthStatus = AgentHealthStatus.UNKNOWN
    policies: AgentPolicies = field(default_factory=lambda: default_agent_policies)
    events: list[AgentEvent] = field(default_factory=list)
    correlation_id: str | None = None
    session_id: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    error_count: int = 0
    last_heartbeat: datetime | None = None
    checkpoint: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def status(self) -> AgentStatus:
        return self.state_machine.current_state

    @property
    def is_healthy(self) -> bool:
        return self.health_status == AgentHealthStatus.HEALTHY

    @property
    def is_active(self) -> bool:
        return self.state_machine.is_active()

    @property
    def is_terminal(self) -> bool:
        return self.state_machine.is_terminal()

    @property
    def can_execute(self) -> bool:
        return self.state_machine.can_execute()

    @property
    def can_modify(self) -> bool:
        return self.state_machine.can_modify()

    def has_capability(self, capability: AgentCapability) -> bool:
        return capability in self.capabilities

    @property
    def elapsed_seconds(self) -> float:
        if self.started_at is None:
            return 0.0
        delta = datetime.now(timezone.utc) - self.started_at
        return delta.total_seconds()

    def _record_event(self, event: AgentEvent) -> None:
        event.agent_id = str(self.agent_id)
        event.correlation_id = self.correlation_id or ""
        self.events.append(event)

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1

    def initialize(self, session_id: str = "") -> None:
        if self.state_machine.current_state != AgentStatus.CREATED:
            raise IllegalAgentTransitionError(
                from_state=self.status,
                to_state=AgentStatus.INITIALIZED,
            )
        event = self.state_machine.transition_to(AgentStatus.INITIALIZED)
        if event:
            self._record_event(event)
        self._record_event(
            AgentCreated(
                agent_id=str(self.agent_id),
                agent_type=self.agent_type.value,
                name=self.name,
            )
        )
        self.session_id = session_id or str(self.agent_id)
        self._touch()

    def start(self) -> None:
        if self.state_machine.current_state not in (
            AgentStatus.INITIALIZED, AgentStatus.PAUSED, AgentStatus.WAITING,
        ):
            raise IllegalAgentTransitionError(
                from_state=self.status,
                to_state=AgentStatus.RUNNING,
            )
        event = self.state_machine.transition_to(AgentStatus.RUNNING)
        if event:
            self._record_event(event)
        self._record_event(
            AgentStarted(
                agent_id=str(self.agent_id),
                session_id=self.session_id or "",
            )
        )
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
        self._touch()

    def pause(self, reason: str = "") -> None:
        if self.state_machine.current_state not in (AgentStatus.RUNNING, AgentStatus.WAITING):
            raise IllegalAgentTransitionError(
                from_state=self.status,
                to_state=AgentStatus.PAUSED,
            )
        event = self.state_machine.transition_to(AgentStatus.PAUSED)
        if event:
            self._record_event(event)
        self._record_event(
            AgentPaused(
                agent_id=str(self.agent_id),
                reason=reason,
            )
        )
        self._touch()

    def resume(self, reason: str = "") -> None:
        if self.state_machine.current_state != AgentStatus.PAUSED:
            raise IllegalAgentTransitionError(
                from_state=self.status,
                to_state=AgentStatus.RUNNING,
            )
        event = self.state_machine.transition_to(AgentStatus.RUNNING)
        if event:
            self._record_event(event)
        self._record_event(
            AgentResumed(
                agent_id=str(self.agent_id),
                reason=reason,
            )
        )
        self._touch()

    def complete(self, result: str = "") -> None:
        if self.state_machine.current_state not in (AgentStatus.RUNNING, AgentStatus.WAITING):
            raise IllegalAgentTransitionError(
                from_state=self.status,
                to_state=AgentStatus.COMPLETED,
            )
        event = self.state_machine.transition_to(AgentStatus.COMPLETED)
        if event:
            self._record_event(event)
        self._record_event(
            AgentCompleted(
                agent_id=str(self.agent_id),
                result=result,
            )
        )
        self.completed_at = datetime.now(timezone.utc)
        self._touch()

    def cancel(self, reason: str = "") -> None:
        if not self.state_machine.can_transition_to(AgentStatus.CANCELLED):
            raise IllegalAgentTransitionError(
                from_state=self.status,
                to_state=AgentStatus.CANCELLED,
            )
        event = self.state_machine.transition_to(AgentStatus.CANCELLED)
        if event:
            self._record_event(event)
        self._record_event(
            AgentCancelled(
                agent_id=str(self.agent_id),
                reason=reason,
            )
        )
        self._touch()

    def fail(self, error: str = "", recoverable: bool = False) -> None:
        if not self.state_machine.can_transition_to(AgentStatus.FAILED):
            raise IllegalAgentTransitionError(
                from_state=self.status,
                to_state=AgentStatus.FAILED,
            )
        event = self.state_machine.transition_to(AgentStatus.FAILED)
        if event:
            self._record_event(event)
        self._record_event(
            AgentFailed(
                agent_id=str(self.agent_id),
                error=error,
                recoverable=recoverable,
            )
        )
        self.error_count += 1
        self._touch()

    def archive(self, reason: str = "") -> None:
        if not self.state_machine.can_transition_to(AgentStatus.ARCHIVED):
            raise IllegalAgentTransitionError(
                from_state=self.status,
                to_state=AgentStatus.ARCHIVED,
            )
        event = self.state_machine.transition_to(AgentStatus.ARCHIVED)
        if event:
            self._record_event(event)
        self._record_event(
            AgentArchived(
                agent_id=str(self.agent_id),
                reason=reason,
            )
        )
        self._touch()

    def restart(self, session_id: str = "") -> None:
        if self.state_machine.current_state != AgentStatus.FAILED:
            raise IllegalAgentTransitionError(
                from_state=self.status,
                to_state=AgentStatus.INITIALIZED,
            )
        self.state_machine = AgentStateMachine(AgentStatus.CREATED)
        event = self.state_machine.transition_to(AgentStatus.INITIALIZED)
        if event:
            self._record_event(event)
        self._record_event(
            AgentRestarted(
                agent_id=str(self.agent_id),
                session_id=session_id or str(self.agent_id),
            )
        )
        self.session_id = session_id or str(self.agent_id)
        self.started_at = None
        self.completed_at = None
        self._touch()

    def record_heartbeat(self) -> None:
        self.last_heartbeat = datetime.now(timezone.utc)
        self._record_event(
            AgentHeartbeat(
                agent_id=str(self.agent_id),
                session_id=self.session_id or "",
            )
        )
        self._touch()

    def save_checkpoint(self, data: dict[str, Any]) -> None:
        self.checkpoint = dict(data)
        self._touch()

    def drain_events(self) -> list[AgentEvent]:
        events = list(self.events)
        self.events.clear()
        return events
