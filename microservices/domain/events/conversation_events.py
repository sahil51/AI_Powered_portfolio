from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class ConversationCreatedEvent:
    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    intent: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ConversationEndedEvent:
    conversation_id: str = ""
    summary: str = ""
    ended_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
