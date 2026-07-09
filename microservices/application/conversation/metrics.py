from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ConversationMetrics:
    total_created: int = 0
    total_completed: int = 0
    total_cancelled: int = 0
    total_archived: int = 0
    total_expired: int = 0
    total_messages: int = 0
    active_count: int = 0
    paused_count: int = 0
    average_messages_per_conversation: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "total_created": self.total_created,
            "total_completed": self.total_completed,
            "total_cancelled": self.total_cancelled,
            "total_archived": self.total_archived,
            "total_expired": self.total_expired,
            "total_messages": self.total_messages,
            "active_count": self.active_count,
            "paused_count": self.paused_count,
            "average_messages_per_conversation": round(self.average_messages_per_conversation, 2),
            "last_updated": self.last_updated.isoformat(),
        }
