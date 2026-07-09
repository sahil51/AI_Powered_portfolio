import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_PLACEHOLDER = "tool_placeholder"
    WORKFLOW = "workflow"
    INTERNAL = "internal"


class ParticipantRole(str, Enum):
    OWNER = "owner"
    PARTICIPANT = "participant"
    VIEWER = "viewer"
    SYSTEM = "system"


@dataclass(frozen=True)
class ConversationId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class MessageId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ParticipantId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass
class Attachment:
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Participant:
    participant_id: ParticipantId
    role: ParticipantRole = ParticipantRole.PARTICIPANT
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    left_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return self.left_at is None


@dataclass
class Message:
    message_id: MessageId = field(default_factory=MessageId)
    conversation_id: ConversationId | None = None
    message_type: MessageType = MessageType.USER
    content: str = ""
    participant_id: ParticipantId | None = None
    correlation_id: str | None = None
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    attachments: list[Attachment] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_user_message(self) -> bool:
        return self.message_type == MessageType.USER

    @property
    def is_assistant_message(self) -> bool:
        return self.message_type == MessageType.ASSISTANT

    @property
    def is_system_message(self) -> bool:
        return self.message_type == MessageType.SYSTEM


@dataclass
class ConversationMetadata:
    title: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    source: str = "chat"
    timezone: str = "UTC"
    language: str = "en"
    custom_fields: dict[str, Any] = field(default_factory=dict)
