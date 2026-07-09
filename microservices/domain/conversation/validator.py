
from domain.conversation.aggregate import Conversation
from domain.conversation.policies import ConversationPolicies, default_policies
from domain.conversation.state import ConversationState
from domain.conversation.value_objects import Message, MessageType, Participant, ParticipantRole


class ConversationValidationError(Exception):
    pass


class ConversationValidator:
    def __init__(self, policies: ConversationPolicies | None = None) -> None:
        self._policies = policies or default_policies

    def validate_create(self, user_id: str, session_id: str | None = None) -> None:
        if not user_id or not user_id.strip():
            raise ConversationValidationError("User ID is required")
        if len(user_id) > 255:
            raise ConversationValidationError("User ID exceeds maximum length")
        if session_id is not None and len(session_id) > 255:
            raise ConversationValidationError("Session ID exceeds maximum length")

    def validate_message(self, message: Message) -> None:
        if not message.content and message.message_type != MessageType.SYSTEM:
            raise ConversationValidationError("Message content is required")
        if self._policies.exceeds_max_message_length(len(message.content)):
            raise ConversationValidationError("Message exceeds maximum length")
        if not message.message_type:
            raise ConversationValidationError("Message type is required")
        if message.token_count < 0:
            raise ConversationValidationError("Token count cannot be negative")

    def validate_participant(self, participant: Participant) -> None:
        if not participant.participant_id or not participant.participant_id.value.strip():
            raise ConversationValidationError("Participant ID is required")
        if participant.role not in ParticipantRole:
            raise ConversationValidationError(f"Invalid participant role: {participant.role}")

    def validate_state_transition(self, conversation: Conversation, target: ConversationState) -> bool:
        return conversation.state_machine.can_transition_to(target)

    def validate_ownership(self, conversation: Conversation, user_id: str) -> bool:
        if not self._policies.enforce_ownership:
            return True
        return conversation.user_id == user_id

    def validate_identity(self, conversation: Conversation, identity_source: str) -> bool:
        if conversation.identity_source == "anonymous" and identity_source == "anonymous":
            return True
        if conversation.user_id is not None:
            return True
        return False

    def validate_conversation_expiration(self, conversation: Conversation) -> bool:
        elapsed = conversation.elapsed_since_last_activity()
        return not self._policies.should_timeout(elapsed)

    def validate_duplicate_message(self, conversation: Conversation, content: str) -> bool:
        if not conversation.messages:
            return True
        last_message = conversation.messages[-1]
        return not (last_message.content == content and last_message.message_type == MessageType.USER)

    def validate_message_ordering(self, conversation: Conversation, message: Message) -> bool:
        if not conversation.messages:
            return True
        last_msg = conversation.messages[-1]
        if message.message_type == MessageType.ASSISTANT and last_msg.message_type == MessageType.ASSISTANT:
            return False
        if message.message_type == MessageType.USER and last_msg.message_type == MessageType.USER:
            return False
        return True
