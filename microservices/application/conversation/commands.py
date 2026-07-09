from dataclasses import dataclass, field

from domain.conversation.value_objects import ConversationMetadata, MessageType


@dataclass
class CreateConversationCommand:
    user_id: str
    session_id: str | None = None
    identity_source: str = "anonymous"
    correlation_id: str | None = None
    metadata: ConversationMetadata | None = None


@dataclass
class StoreMessageCommand:
    conversation_id: str
    content: str
    message_type: MessageType = MessageType.USER
    participant_id: str | None = None
    correlation_id: str | None = None
    token_count: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class PauseConversationCommand:
    conversation_id: str
    reason: str = ""
    user_id: str = ""


@dataclass
class ResumeConversationCommand:
    conversation_id: str
    user_id: str = ""


@dataclass
class CompleteConversationCommand:
    conversation_id: str
    summary: str = ""
    user_id: str = ""


@dataclass
class CancelConversationCommand:
    conversation_id: str
    reason: str = ""
    user_id: str = ""


@dataclass
class ArchiveConversationCommand:
    conversation_id: str
    reason: str = ""
