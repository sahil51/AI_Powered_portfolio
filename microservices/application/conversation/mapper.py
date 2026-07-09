from datetime import datetime, timezone

from application.conversation.context import ConversationContext
from domain.conversation.aggregate import Conversation
from domain.conversation.state import ConversationState, ConversationStateMachine
from domain.conversation.value_objects import (
    Attachment,
    ConversationId,
    ConversationMetadata,
    Message,
    MessageId,
    MessageType,
    Participant,
    ParticipantId,
    ParticipantRole,
)


class ConversationMapper:
    @staticmethod
    def context_to_conversation(ctx: ConversationContext) -> Conversation:
        return Conversation(
            conversation_id=ConversationId(),
            user_id=ctx.user_id,
            session_id=ctx.session_id or "",
            identity_source=ctx.identity_source,
            correlation_id=ctx.correlation_id,
        )

    @staticmethod
    def to_dict(conversation: Conversation) -> dict:
        return {
            "conversation_id": str(conversation.conversation_id),
            "user_id": conversation.user_id,
            "session_id": conversation.session_id,
            "identity_source": conversation.identity_source,
            "state": conversation.state.value,
            "message_count": conversation.message_count,
            "participant_count": conversation.participant_count,
            "summary": conversation.summary,
            "correlation_id": conversation.correlation_id,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            "last_activity_at": conversation.last_activity_at.isoformat() if conversation.last_activity_at else None,
            "completed_at": conversation.completed_at.isoformat() if conversation.completed_at else None,
            "version": conversation.version,
            "messages": [ConversationMapper.message_to_dict(m) for m in conversation.messages],
            "participants": [ConversationMapper.participant_to_dict(p) for p in conversation.participants],
            "metadata": ConversationMapper.metadata_to_dict(conversation.metadata),
        }

    @staticmethod
    def message_to_dict(message: Message) -> dict:
        return {
            "message_id": str(message.message_id),
            "conversation_id": str(message.conversation_id) if message.conversation_id else None,
            "message_type": message.message_type.value,
            "content": message.content,
            "participant_id": str(message.participant_id) if message.participant_id else None,
            "correlation_id": message.correlation_id,
            "token_count": message.token_count,
            "metadata": message.metadata,
            "attachments": [ConversationMapper.attachment_to_dict(a) for a in message.attachments],
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }

    @staticmethod
    def participant_to_dict(participant: Participant) -> dict:
        return {
            "participant_id": str(participant.participant_id),
            "role": participant.role.value,
            "joined_at": participant.joined_at.isoformat() if participant.joined_at else None,
            "left_at": participant.left_at.isoformat() if participant.left_at else None,
            "is_active": participant.is_active,
            "metadata": participant.metadata,
        }

    @staticmethod
    def attachment_to_dict(attachment: Attachment) -> dict:
        return {
            "filename": attachment.filename,
            "content_type": attachment.content_type,
            "size_bytes": attachment.size_bytes,
            "storage_path": attachment.storage_path,
        }

    @staticmethod
    def metadata_to_dict(metadata: ConversationMetadata) -> dict:
        return {
            "title": metadata.title,
            "description": metadata.description,
            "tags": metadata.tags,
            "source": metadata.source,
            "timezone": metadata.timezone,
            "language": metadata.language,
            "custom_fields": metadata.custom_fields,
        }

    @staticmethod
    def dict_to_conversation(data: dict) -> Conversation:
        conv = Conversation(
            conversation_id=ConversationId(),
            user_id=data.get("user_id", ""),
            session_id=data.get("session_id", ""),
            identity_source=data.get("identity_source", "anonymous"),
            state_machine=ConversationStateMachine(
                ConversationState(data.get("state", "created")),
            ),
            correlation_id=data.get("correlation_id"),
        )
        if "summary" in data:
            conv.summary = data["summary"]
        if "metadata" in data:
            conv.metadata = ConversationMapper.dict_to_metadata(data["metadata"])
        if "messages" in data:
            conv.messages = [ConversationMapper.dict_to_message(m) for m in data["messages"]]
        if "participants" in data:
            conv.participants = [ConversationMapper.dict_to_participant(p) for p in data["participants"]]
        return conv

    @staticmethod
    def dict_to_message(data: dict) -> Message:
        return Message(
            message_id=MessageId(),
            message_type=MessageType(data.get("message_type", "user")),
            content=data.get("content", ""),
            participant_id=ParticipantId(data["participant_id"]) if data.get("participant_id") else None,
            correlation_id=data.get("correlation_id"),
            token_count=data.get("token_count", 0),
            metadata=data.get("metadata", {}),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at") else datetime.now(timezone.utc)
            ),
        )

    @staticmethod
    def dict_to_participant(data: dict) -> Participant:
        return Participant(
            participant_id=ParticipantId(value=data["participant_id"]),
            role=ParticipantRole(data.get("role", "participant")),
            metadata=data.get("metadata", {}),
        )

    @staticmethod
    def dict_to_metadata(data: dict) -> ConversationMetadata:
        return ConversationMetadata(
            title=data.get("title"),
            description=data.get("description"),
            tags=data.get("tags", []),
            source=data.get("source", "chat"),
            timezone=data.get("timezone", "UTC"),
            language=data.get("language", "en"),
            custom_fields=data.get("custom_fields", {}),
        )
