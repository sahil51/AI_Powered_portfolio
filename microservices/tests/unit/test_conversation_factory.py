import pytest

from domain.conversation.factory import ConversationFactory
from domain.conversation.state import ConversationState
from domain.conversation.validator import ConversationValidationError
from domain.conversation.value_objects import ConversationMetadata, ParticipantRole


class TestConversationFactory:
    def setup_method(self) -> None:
        self.factory = ConversationFactory()

    def test_create_conversation(self):
        conv = self.factory.create(user_id="user-1", session_id="session-1")
        assert conv.user_id == "user-1"
        assert conv.session_id == "session-1"
        assert conv.state == ConversationState.ACTIVE
        assert conv.participant_count >= 1

    def test_create_conversation_with_metadata(self):
        metadata = ConversationMetadata(title="Test", tags=["support"])
        conv = self.factory.create(
            user_id="user-1",
            session_id="session-1",
            metadata=metadata,
        )
        assert conv.metadata.title == "Test"
        assert "support" in conv.metadata.tags

    def test_create_conversation_creates_owner(self):
        conv = self.factory.create(user_id="user-1")
        assert conv.participant_count == 1
        owner = conv.participants[0]
        assert str(owner.participant_id) == "user-1"
        assert owner.role == ParticipantRole.OWNER

    def test_create_conversation_invalid_user(self):
        with pytest.raises(ConversationValidationError):
            self.factory.create(user_id="")

    def test_create_with_correlation_id(self):
        conv = self.factory.create(user_id="user-1", correlation_id="corr-1")
        assert conv.correlation_id == "corr-1"

    def test_create_with_identity_source(self):
        conv = self.factory.create(user_id="user-1", identity_source="jwt")
        assert conv.identity_source == "jwt"

    def test_create_with_session(self):
        conv = self.factory.create(user_id="user-1", session_id="session-abc")
        assert conv.session_id == "session-abc"

    def test_activate_emits_event(self):
        conv = self.factory.create(user_id="user-1")
        events = conv.drain_events()
        event_names = [type(e).__name__ for e in events]
        assert "ConversationCreated" in event_names or "ConversationActivated" in event_names
