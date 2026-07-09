from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from domain.conversation.events import (
    ConversationCancelled,
    ConversationCompleted,
    ConversationCreated,
    ConversationEvent,
    ConversationExpired,
    ConversationPaused,
    MessageReceived,
    MessageStored,
)
from domain.conversation.policies import ConversationPolicies, default_policies
from domain.conversation.state import ConversationState, ConversationStateMachine, IllegalStateTransitionError
from domain.conversation.value_objects import (
    ConversationId,
    ConversationMetadata,
    Message,
    MessageType,
    Participant,
    ParticipantId,
)


@dataclass
class Conversation:
    conversation_id: ConversationId = field(default_factory=ConversationId)
    user_id: str = ""
    session_id: str = ""
    identity_source: str = "anonymous"
    state_machine: ConversationStateMachine = field(default_factory=ConversationStateMachine)
    messages: list[Message] = field(default_factory=list)
    participants: list[Participant] = field(default_factory=list)
    metadata: ConversationMetadata = field(default_factory=ConversationMetadata)
    policies: ConversationPolicies = field(default_factory=lambda: default_policies)
    events: list[ConversationEvent] = field(default_factory=list)
    summary: str | None = None
    correlation_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    paused_at: datetime | None = None
    completed_at: datetime | None = None
    version: int = 1

    @property
    def state(self) -> ConversationState:
        return self.state_machine.current_state

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def participant_count(self) -> int:
        return len(self.participants)

    @property
    def is_active(self) -> bool:
        return self.state in (
            ConversationState.ACTIVE,
            ConversationState.COLLECTING_INFORMATION,
            ConversationState.WAITING_CONFIRMATION,
            ConversationState.WAITING_EXTERNAL_WORKFLOW,
            ConversationState.RESUMED,
        )

    @property
    def is_paused(self) -> bool:
        return self.state == ConversationState.PAUSED

    @property
    def is_terminal(self) -> bool:
        return self.state_machine.is_terminal()

    def _record_event(self, event: ConversationEvent) -> None:
        event.conversation_id = str(self.conversation_id)
        event.correlation_id = self.correlation_id or ""
        self.events.append(event)

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
        self.last_activity_at = datetime.now(timezone.utc)
        self.version += 1

    def activate(self) -> None:
        event = self.state_machine.transition_to(ConversationState.ACTIVE)
        if event:
            self._record_event(event)
        if not self.events:
            self._record_event(
                ConversationCreated(
                    conversation_id=str(self.conversation_id),
                    user_id=self.user_id,
                    session_id=self.session_id,
                    identity_source=self.identity_source,
                )
            )
        self._touch()

    def add_message(self, message: Message) -> None:
        if not self.state_machine.can_accept_messages():
            raise IllegalStateTransitionError(
                from_state=self.state,
                to_state=self.state,
            )
        if self.policies.exceeds_max_messages(self.message_count):
            raise ConversationPolicyError("Maximum message count reached")
        if self.policies.exceeds_max_message_length(len(message.content)):
            raise ConversationPolicyError("Message exceeds maximum length")

        message.conversation_id = self.conversation_id
        self.messages.append(message)
        self._record_event(
            MessageReceived(
                conversation_id=str(self.conversation_id),
                message_id=str(message.message_id),
                message_type=message.message_type.value,
                content=message.content[:200],
                participant_id=str(message.participant_id) if message.participant_id else "",
                token_count=message.token_count,
            )
        )
        self._record_event(
            MessageStored(
                conversation_id=str(self.conversation_id),
                message_id=str(message.message_id),
                message_type=message.message_type.value,
                content_preview=message.content[:100],
                participant_id=str(message.participant_id) if message.participant_id else "",
                token_count=message.token_count,
            )
        )
        self._touch()

    def pause(self, reason: str = "") -> None:
        event = self.state_machine.transition_to(ConversationState.PAUSED)
        if event:
            self._record_event(event)
        self.paused_at = datetime.now(timezone.utc)
        if isinstance(self.events[-1], ConversationPaused):
            self.events[-1].reason = reason
        self._touch()

    def resume(self) -> None:
        event = self.state_machine.transition_to(ConversationState.RESUMED)
        if event:
            self._record_event(event)
        self.paused_at = None
        self.state_machine.transition_to(ConversationState.ACTIVE)
        self._touch()

    def complete(self, summary: str = "") -> None:
        event = self.state_machine.transition_to(ConversationState.COMPLETED)
        if event:
            self._record_event(event)
        self.summary = summary
        self.completed_at = datetime.now(timezone.utc)
        if isinstance(self.events[-1], ConversationCompleted):
            self.events[-1].summary = summary
            self.events[-1].message_count = self.message_count
        self._touch()

    def cancel(self, reason: str = "") -> None:
        event = self.state_machine.transition_to(ConversationState.CANCELLED)
        if event:
            self._record_event(event)
        if isinstance(self.events[-1], ConversationCancelled):
            self.events[-1].reason = reason
        self._touch()

    def archive(self, reason: str = "") -> None:
        event = self.state_machine.transition_to(ConversationState.ARCHIVED)
        if event:
            self._record_event(event)
        if isinstance(self.events[-1], ConversationCancelled):
            self.events[-1].reason = reason
        self._touch()

    def expire(self) -> None:
        self._record_event(
            ConversationExpired(
                conversation_id=str(self.conversation_id),
            )
        )
        self._touch()

    def add_participant(self, participant: Participant) -> None:
        if self.policies.exceeds_max_participants(self.participant_count):
            raise ConversationPolicyError("Maximum participant count reached")
        if any(p.participant_id == participant.participant_id for p in self.participants):
            raise ConversationPolicyError("Participant already exists")
        self.participants.append(participant)
        self._touch()

    def remove_participant(self, participant_id: ParticipantId) -> None:
        self.participants = [p for p in self.participants if p.participant_id != participant_id]
        self._touch()

    def get_messages(self, message_type: MessageType | None = None) -> list[Message]:
        if message_type is None:
            return list(self.messages)
        return [m for m in self.messages if m.message_type == message_type]

    def elapsed_since_last_activity(self) -> float:
        delta = datetime.now(timezone.utc) - self.last_activity_at
        return delta.total_seconds() / 60.0

    def elapsed_since_paused(self) -> float | None:
        if self.paused_at is None:
            return None
        delta = datetime.now(timezone.utc) - self.paused_at
        return delta.total_seconds() / 60.0

    def drain_events(self) -> list[ConversationEvent]:
        events = list(self.events)
        self.events.clear()
        return events


class ConversationPolicyError(Exception):
    pass
