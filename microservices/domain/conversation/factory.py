from domain.conversation.aggregate import Conversation
from domain.conversation.policies import ConversationPolicies, default_policies
from domain.conversation.state import ConversationState, ConversationStateMachine
from domain.conversation.validator import ConversationValidator
from domain.conversation.value_objects import (
    ConversationId,
    ConversationMetadata,
    Participant,
    ParticipantId,
    ParticipantRole,
)


class ConversationFactory:
    def __init__(self, validator: ConversationValidator | None = None) -> None:
        self._validator = validator or ConversationValidator()

    def create(
        self,
        user_id: str,
        session_id: str | None = None,
        identity_source: str = "anonymous",
        metadata: ConversationMetadata | None = None,
        policies: ConversationPolicies | None = None,
        correlation_id: str | None = None,
    ) -> Conversation:
        self._validator.validate_create(user_id, session_id)

        conversation = Conversation(
            conversation_id=ConversationId(),
            user_id=user_id,
            session_id=session_id or "",
            identity_source=identity_source,
            state_machine=ConversationStateMachine(ConversationState.CREATED),
            metadata=metadata or ConversationMetadata(),
            policies=policies or default_policies,
            correlation_id=correlation_id,
        )

        owner = Participant(
            participant_id=ParticipantId(value=user_id),
            role=ParticipantRole.OWNER,
        )
        conversation.add_participant(owner)
        conversation.activate()

        return conversation

    def restore(
        self,
        conversation_id: str,
        user_id: str,
        session_id: str,
        identity_source: str,
        state: ConversationState,
        messages: list | None = None,
        participants: list | None = None,
        metadata: ConversationMetadata | None = None,
        summary: str | None = None,
        correlation_id: str | None = None,
        created_at: object = None,
        updated_at: object = None,
        last_activity_at: object = None,
        paused_at: object = None,
        completed_at: object = None,
        version: int = 1,
    ) -> Conversation:
        import datetime

        conv = Conversation(
            conversation_id=ConversationId() if not conversation_id else type("obj", (), {"value": conversation_id})(),
            user_id=user_id,
            session_id=session_id,
            identity_source=identity_source,
            state_machine=ConversationStateMachine(state),
            metadata=metadata or ConversationMetadata(),
            summary=summary,
            correlation_id=correlation_id,
            created_at=created_at or datetime.datetime.now(datetime.timezone.utc),
            updated_at=updated_at or datetime.datetime.now(datetime.timezone.utc),
            last_activity_at=last_activity_at or datetime.datetime.now(datetime.timezone.utc),
            paused_at=paused_at,
            completed_at=completed_at,
            version=version,
        )
        if messages:
            conv.messages = list(messages)
        if participants:
            conv.participants = list(participants)
        return conv
