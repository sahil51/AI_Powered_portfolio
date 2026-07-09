from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ConversationEvent:
    event_id: str = ""
    conversation_id: str = ""
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationCreated(ConversationEvent):
    user_id: str = ""
    session_id: str = ""
    identity_source: str = "anonymous"


@dataclass
class ConversationActivated(ConversationEvent):
    pass


@dataclass
class MessageReceived(ConversationEvent):
    message_id: str = ""
    message_type: str = ""
    content: str = ""
    participant_id: str = ""
    token_count: int = 0


@dataclass
class MessageStored(ConversationEvent):
    message_id: str = ""
    message_type: str = ""
    content_preview: str = ""
    participant_id: str = ""
    token_count: int = 0


@dataclass
class ConversationPaused(ConversationEvent):
    reason: str = ""


@dataclass
class ConversationResumed(ConversationEvent):
    pass


@dataclass
class ConversationCompleted(ConversationEvent):
    summary: str = ""
    message_count: int = 0


@dataclass
class ConversationCancelled(ConversationEvent):
    reason: str = ""


@dataclass
class ConversationArchived(ConversationEvent):
    reason: str = ""


@dataclass
class ConversationExpired(ConversationEvent):
    reason: str = "timeout"
