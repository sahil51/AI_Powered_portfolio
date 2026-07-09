from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class MeetingScheduledEvent:
    meeting_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    user_email: str = ""
    meeting_type: str = ""
    scheduled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: dict = field(default_factory=dict)


@dataclass
class MeetingCancelledEvent:
    meeting_id: str = ""
    reason: str = ""
    cancelled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MeetingRescheduledEvent:
    meeting_id: str = ""
    old_time: datetime | None = None
    new_time: datetime | None = None
    rescheduled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
