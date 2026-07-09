import json

from application.conversation.mapper import ConversationMapper
from domain.conversation.aggregate import Conversation
from domain.conversation.events import ConversationEvent
from domain.conversation.value_objects import (
    Message,
)


class ConversationSerializer:
    @staticmethod
    def serialize(conversation: Conversation) -> str:
        data = ConversationMapper.to_dict(conversation)
        return json.dumps(data, default=str)

    @staticmethod
    def deserialize(data: str) -> Conversation:
        raw = json.loads(data)
        return ConversationMapper.dict_to_conversation(raw)

    @staticmethod
    def serialize_messages(messages: list[Message]) -> str:
        data = [ConversationMapper.message_to_dict(m) for m in messages]
        return json.dumps(data, default=str)

    @staticmethod
    def deserialize_messages(data: str) -> list[Message]:
        raw = json.loads(data)
        return [ConversationMapper.dict_to_message(m) for m in raw]

    @staticmethod
    def serialize_events(events: list[ConversationEvent]) -> str:
        data = []
        for event in events:
            ev = {"event_type": type(event).__name__}
            ev.update({k: str(v) if hasattr(v, "isoformat") else v for k, v in event.__dict__.items()})
            data.append(ev)
        return json.dumps(data, default=str)

    @staticmethod
    def to_json_dict(conversation: Conversation) -> dict:
        return ConversationMapper.to_dict(conversation)

    @staticmethod
    def summary_to_dict(conversation: Conversation) -> dict:
        return {
            "conversation_id": str(conversation.conversation_id),
            "state": conversation.state.value,
            "message_count": conversation.message_count,
            "participant_count": conversation.participant_count,
            "last_activity_at": conversation.last_activity_at.isoformat() if conversation.last_activity_at else None,
            "summary": conversation.summary,
            "metadata_title": conversation.metadata.title,
        }
