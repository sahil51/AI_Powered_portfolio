from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.meeting.events import (
    MeetingEvent,
    MeetingFieldCollected,
)
from domain.meeting.policies import MeetingPolicies, default_meeting_policies
from domain.meeting.state import MeetingStateMachine, MeetingStatus
from domain.meeting.value_objects import (
    MeetingField,
    MeetingFieldStatus,
    MeetingId,
    MeetingMetadata,
)


@dataclass
class Meeting:
    meeting_id: MeetingId = field(default_factory=MeetingId)
    title: str = ""
    user_id: str = ""
    conversation_id: str = ""
    session_id: str = ""
    fields: list[MeetingField] = field(default_factory=list)
    state_machine: MeetingStateMachine = field(default_factory=MeetingStateMachine)
    policies: MeetingPolicies = field(default_factory=lambda: default_meeting_policies)
    metadata: MeetingMetadata = field(default_factory=MeetingMetadata)
    events: list[MeetingEvent] = field(default_factory=list)
    correlation_id: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    workflow_id: str = ""
    error: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    version: int = 1

    @property
    def status(self) -> MeetingStatus:
        return self.state_machine.current_state

    @property
    def is_active(self) -> bool:
        return self.state_machine.is_active()

    @property
    def is_terminal(self) -> bool:
        return self.state_machine.is_terminal()

    @property
    def can_collect(self) -> bool:
        return self.state_machine.can_collect()

    @property
    def can_submit(self) -> bool:
        return self.state_machine.can_submit()

    @property
    def collected_fields(self) -> dict[str, str]:
        return {
            f.name: f.value or ""
            for f in self.fields
            if f.is_collected and f.value
        }

    @property
    def collected_field_names(self) -> list[str]:
        return [f.name for f in self.fields if f.is_collected]

    @property
    def missing_fields(self) -> list[MeetingField]:
        return [f for f in self.fields if f.required and not f.is_collected]

    @property
    def missing_field_names(self) -> list[str]:
        return [f.name for f in self.missing_fields]

    @property
    def next_field(self) -> MeetingField | None:
        ordered = sorted(self.fields, key=lambda f: f.order)
        for f in ordered:
            if f.required and not f.is_collected:
                return f
        for f in ordered:
            if not f.required and not f.is_collected:
                return f
        return None

    @property
    def ready_for_workflow(self) -> bool:
        return self.status == MeetingStatus.READY and len(self.missing_fields) == 0

    def _record_event(self, event: MeetingEvent) -> None:
        self.events.append(event)

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1

    def start_collecting(self) -> None:
        event = self.state_machine.transition_to(MeetingStatus.COLLECTING_INFORMATION)
        if event:
            self._record_event(event)
        self._touch()

    def collect_field(self, name: str, value: str) -> None:
        for f in self.fields:
            if f.name == name:
                f.value = value
                f.status = MeetingFieldStatus.COLLECTED
                break
        self._record_event(MeetingFieldCollected(
            meeting_id=str(self.meeting_id),
            field_name=name,
            field_value=value,
        ))
        self._touch()

    def request_confirmation(self) -> None:
        event = self.state_machine.transition_to(MeetingStatus.WAITING_CONFIRMATION)
        if event:
            self._record_event(event)
        self._touch()

    def confirm(self) -> None:
        for f in self.fields:
            if f.status == MeetingFieldStatus.COLLECTED:
                f.status = MeetingFieldStatus.CONFIRMED
        event = self.state_machine.transition_to(MeetingStatus.READY)
        if event:
            self._record_event(event)
        self._touch()

    def correct_field(self, name: str, value: str) -> None:
        for f in self.fields:
            if f.name == name:
                f.value = value
                f.status = MeetingFieldStatus.CORRECTED
                break
        self._record_event(MeetingFieldCollected(
            meeting_id=str(self.meeting_id),
            field_name=name,
            field_value=value,
        ))
        self._touch()

    def submit(self, workflow_id: str) -> None:
        event = self.state_machine.transition_to(MeetingStatus.SUBMITTED)
        if event:
            self._record_event(event)
        self.workflow_id = workflow_id
        self._touch()

    def complete(self, result: str = "") -> None:
        event = self.state_machine.transition_to(MeetingStatus.COMPLETED)
        if event:
            self._record_event(event)
        self.completed_at = datetime.now(timezone.utc)
        self._touch()

    def cancel(self, reason: str = "") -> None:
        event = self.state_machine.transition_to(MeetingStatus.CANCELLED)
        if event:
            self._record_event(event)
        self._touch()

    def fail(self, error: str = "", recoverable: bool = False) -> None:
        event = self.state_machine.transition_to(MeetingStatus.FAILED)
        if event:
            self._record_event(event)
        self.error = error
        self._touch()

    def archive(self, reason: str = "") -> None:
        event = self.state_machine.transition_to(MeetingStatus.ARCHIVED)
        if event:
            self._record_event(event)
        self._touch()

    def resume_collecting(self) -> None:
        event = self.state_machine.transition_to(MeetingStatus.COLLECTING_INFORMATION)
        if event:
            self._record_event(event)
        self._touch()

    def drain_events(self) -> list[MeetingEvent]:
        drained = list(self.events)
        self.events.clear()
        return drained
