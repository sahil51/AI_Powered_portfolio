
from domain.conversation.events import (
    ConversationActivated,
    ConversationArchived,
    ConversationCancelled,
    ConversationCompleted,
    ConversationCreated,
    ConversationEvent,
    ConversationExpired,
    ConversationPaused,
    ConversationResumed,
    MessageReceived,
    MessageStored,
)


class TestConversationEvents:
    def test_conversation_created_event(self):
        event = ConversationCreated(conversation_id="conv-1", user_id="user-1")
        assert event.conversation_id == "conv-1"
        assert event.user_id == "user-1"
        assert event.identity_source == "anonymous"
        assert event.event_id == ""

    def test_conversation_activated_event(self):
        event = ConversationActivated(conversation_id="conv-1")
        assert isinstance(event, ConversationEvent)

    def test_message_received_event(self):
        event = MessageReceived(
            conversation_id="conv-1",
            message_id="msg-1",
            message_type="user",
            content="Hello",
        )
        assert event.message_type == "user"
        assert event.content == "Hello"

    def test_message_stored_event(self):
        event = MessageStored(
            conversation_id="conv-1",
            message_id="msg-1",
            message_type="user",
            content_preview="Hel...",
        )
        assert event.content_preview == "Hel..."

    def test_conversation_paused_event(self):
        event = ConversationPaused(conversation_id="conv-1", reason="Need info")
        assert event.reason == "Need info"

    def test_conversation_resumed_event(self):
        event = ConversationResumed(conversation_id="conv-1")
        assert isinstance(event, ConversationEvent)

    def test_conversation_completed_event(self):
        event = ConversationCompleted(conversation_id="conv-1", summary="Done", message_count=5)
        assert event.summary == "Done"
        assert event.message_count == 5

    def test_conversation_cancelled_event(self):
        event = ConversationCancelled(conversation_id="conv-1", reason="Cancelled")
        assert event.reason == "Cancelled"

    def test_conversation_archived_event(self):
        event = ConversationArchived(conversation_id="conv-1", reason="Archived")
        assert event.reason == "Archived"

    def test_conversation_expired_event(self):
        event = ConversationExpired(conversation_id="conv-1")
        assert event.reason == "timeout"

    def test_event_has_timestamp(self):
        event = ConversationCreated(conversation_id="conv-1")
        assert event.timestamp is not None

    def test_event_metadata(self):
        event = ConversationCreated(conversation_id="conv-1", metadata={"source": "web"})
        assert event.metadata["source"] == "web"
