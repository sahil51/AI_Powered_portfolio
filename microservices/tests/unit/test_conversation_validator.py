import pytest

from domain.conversation.aggregate import Conversation
from domain.conversation.policies import ConversationPolicies
from domain.conversation.state import ConversationState
from domain.conversation.validator import ConversationValidationError, ConversationValidator
from domain.conversation.value_objects import (
    ConversationId,
    Message,
    MessageType,
    Participant,
    ParticipantId,
    ParticipantRole,
)


class TestConversationValidator:
    def setup_method(self) -> None:
        self.validator = ConversationValidator()

    def test_validate_create_valid(self):
        self.validator.validate_create("user-1")
        self.validator.validate_create("user-1", "session-1")

    def test_validate_create_empty_user_id(self):
        with pytest.raises(ConversationValidationError, match="User ID is required"):
            self.validator.validate_create("")

    def test_validate_create_whitespace_user_id(self):
        with pytest.raises(ConversationValidationError, match="User ID is required"):
            self.validator.validate_create("   ")

    def test_validate_message_valid(self):
        msg = Message(content="Hello", message_type=MessageType.USER)
        self.validator.validate_message(msg)

    def test_validate_message_empty_content(self):
        msg = Message(content="", message_type=MessageType.USER)
        with pytest.raises(ConversationValidationError, match="Message content is required"):
            self.validator.validate_message(msg)

    def test_validate_message_exceeds_length(self):
        long_content = "x" * 10001
        msg = Message(content=long_content, message_type=MessageType.USER)
        with pytest.raises(ConversationValidationError, match="Message exceeds maximum length"):
            self.validator.validate_message(msg)

    def test_validate_message_negative_token_count(self):
        msg = Message(content="Hello", message_type=MessageType.USER, token_count=-1)
        with pytest.raises(ConversationValidationError, match="Token count cannot be negative"):
            self.validator.validate_message(msg)

    def test_validate_message_no_type(self):
        msg = Message(content="Hello", message_type="")  # type: ignore[arg-type]
        with pytest.raises(ConversationValidationError, match="Message type is required"):
            self.validator.validate_message(msg)

    def test_validate_participant_valid(self):
        participant = Participant(
            participant_id=ParticipantId(value="user-1"),
            role=ParticipantRole.OWNER,
        )
        self.validator.validate_participant(participant)

    def test_validate_participant_empty_id(self):
        participant = Participant(
            participant_id=ParticipantId(value=""),
            role=ParticipantRole.OWNER,
        )
        with pytest.raises(ConversationValidationError, match="Participant ID is required"):
            self.validator.validate_participant(participant)

    def test_validate_participant_invalid_role(self):
        participant = Participant(
            participant_id=ParticipantId(value="user-1"),
            role="admin",  # type: ignore[arg-type]
        )
        with pytest.raises(ConversationValidationError, match="Invalid participant role"):
            self.validator.validate_participant(participant)

    def test_state_transition_valid(self):
        conv = self._make_conversation()
        assert self.validator.validate_state_transition(conv, ConversationState.ACTIVE)
        assert not self.validator.validate_state_transition(conv, ConversationState.COMPLETED)

    def test_ownership_valid(self):
        conv = self._make_conversation(user_id="user-1")
        assert self.validator.validate_ownership(conv, "user-1")
        assert not self.validator.validate_ownership(conv, "user-2")

    def test_ownership_disabled(self):
        policies = ConversationPolicies(enforce_ownership=False)
        validator = ConversationValidator(policies)
        conv = self._make_conversation(user_id="user-1")
        assert validator.validate_ownership(conv, "user-2")

    def test_duplicate_message_detection(self):
        conv = self._make_conversation(user_id="user-1")
        from domain.conversation.state import ConversationStateMachine
        conv.state_machine = ConversationStateMachine(ConversationState.ACTIVE)
        conv.add_message(Message(content="Hello", message_type=MessageType.USER))
        assert not self.validator.validate_duplicate_message(conv, "Hello")
        assert self.validator.validate_duplicate_message(conv, "Hello!")

    def test_message_ordering(self):
        conv = self._make_conversation(user_id="user-1")
        from domain.conversation.state import ConversationStateMachine
        conv.state_machine = ConversationStateMachine(ConversationState.ACTIVE)
        conv.add_message(Message(content="Hello", message_type=MessageType.USER))
        assert self.validator.validate_message_ordering(conv, Message(content="Hi", message_type=MessageType.ASSISTANT))
        assert not self.validator.validate_message_ordering(conv, Message(content="Hey", message_type=MessageType.USER))

    def test_identity_validation_anonymous(self):
        conv = self._make_conversation()
        assert self.validator.validate_identity(conv, "anonymous")

    @staticmethod
    def _make_conversation(user_id: str = "test-user") -> Conversation:
        return Conversation(
            conversation_id=ConversationId(),
            user_id=user_id,
            session_id="session-1",
            identity_source="anonymous",
        )
