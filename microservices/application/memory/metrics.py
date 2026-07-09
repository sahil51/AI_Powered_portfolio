from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MemoryMetrics:
    total_created: int = 0
    total_active: int = 0
    total_archived: int = 0
    total_expired: int = 0
    total_deleted: int = 0
    total_merged: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    by_scope: dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "total_created": self.total_created,
            "total_active": self.total_active,
            "total_archived": self.total_archived,
            "total_expired": self.total_expired,
            "total_deleted": self.total_deleted,
            "total_merged": self.total_merged,
            "by_category": self.by_category,
            "by_scope": self.by_scope,
            "last_updated": self.last_updated.isoformat(),
        }
