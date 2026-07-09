
from application.conversation.mapper import ConversationMapper
from application.conversation.serializer import ConversationSerializer
from domain.conversation.aggregate import Conversation
from domain.conversation.state import ConversationState
from domain.conversation.value_objects import (
    ConversationId,
    ConversationMetadata,
    Message,
    MessageType,
    Participant,
    ParticipantId,
    ParticipantRole,
)


class TestConversationMapper:
    def test_to_dict(self):
        conv = self._make_conversation()
        data = ConversationMapper.to_dict(conv)
        assert data["user_id"] == "user-1"
        assert data["state"] == "created"
        assert "messages" in data
        assert "participants" in data
        assert "metadata" in data

    def test_message_to_dict(self):
        msg = Message(content="Hello", message_type=MessageType.USER, token_count=10)
        data = ConversationMapper.message_to_dict(msg)
        assert data["content"] == "Hello"
        assert data["message_type"] == "user"
        assert data["token_count"] == 10

    def test_participant_to_dict(self):
        participant = Participant(
            participant_id=ParticipantId(value="user-1"),
            role=ParticipantRole.OWNER,
        )
        data = ConversationMapper.participant_to_dict(participant)
        assert data["participant_id"] == "user-1"
        assert data["role"] == "owner"
        assert data["is_active"] is True

    def test_metadata_to_dict(self):
        metadata = ConversationMetadata(title="Test", tags=["a", "b"], source="web")
        data = ConversationMapper.metadata_to_dict(metadata)
        assert data["title"] == "Test"
        assert data["tags"] == ["a", "b"]
        assert data["source"] == "web"

    def test_to_dict_with_messages(self):
        conv = self._make_conversation()
        conv.activate()
        conv.add_message(Message(content="Hello", message_type=MessageType.USER))
        conv.add_message(Message(content="Hi", message_type=MessageType.ASSISTANT))
        data = ConversationMapper.to_dict(conv)
        assert len(data["messages"]) == 2

    def test_dict_to_conversation(self):
        conv = self._make_conversation()
        data = ConversationMapper.to_dict(conv)
        restored = ConversationMapper.dict_to_conversation(data)
        assert restored.user_id == "user-1"
        assert restored.identity_source == "anonymous"

    @staticmethod
    def _make_conversation() -> Conversation:
        return Conversation(
            conversation_id=ConversationId(),
            user_id="user-1",
            session_id="session-1",
            identity_source="anonymous",
        )


class TestConversationSerializer:
    def test_serialize_deserialize(self):
        conv = self._make_conversation()
        conv.activate()
        conv.add_message(Message(content="Hello", message_type=MessageType.USER))

        serialized = ConversationSerializer.serialize(conv)
        assert isinstance(serialized, str)

        deserialized = ConversationSerializer.deserialize(serialized)
        assert deserialized.user_id == "user-1"
        assert deserialized.state == ConversationState.ACTIVE

    def test_summary_to_dict(self):
        conv = self._make_conversation()
        conv.activate()
        conv.complete(summary="All good")
        summary = ConversationSerializer.summary_to_dict(conv)
        assert summary["conversation_id"] == str(conv.conversation_id)
        assert summary["state"] == "completed"
        assert summary["summary"] == "All good"

    def test_serialize_messages(self):
        messages = [
            Message(content="Hello", message_type=MessageType.USER),
            Message(content="Hi", message_type=MessageType.ASSISTANT),
        ]
        serialized = ConversationSerializer.serialize_messages(messages)
        deserialized = ConversationSerializer.deserialize_messages(serialized)
        assert len(deserialized) == 2
        assert deserialized[0].content == "Hello"
        assert deserialized[1].content == "Hi"

    def test_to_json_dict(self):
        conv = self._make_conversation()
        data = ConversationSerializer.to_json_dict(conv)
        assert "conversation_id" in data
        assert "state" in data
        assert "messages" in data

    @staticmethod
    def _make_conversation() -> Conversation:
        conv = Conversation(
            conversation_id=ConversationId(),
            user_id="user-1",
            session_id="session-1",
            identity_source="anonymous",
        )
        return conv
