from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class MeetingEvent:
    meeting_id: str = ""
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MeetingCreated(MeetingEvent):
    pass


@dataclass
class MeetingCollectingStarted(MeetingEvent):
    pass


@dataclass
class MeetingFieldCollected(MeetingEvent):
    field_name: str = ""
    field_value: str = ""


@dataclass
class MeetingWaitingConfirmation(MeetingEvent):
    pass


@dataclass
class MeetingConfirmed(MeetingEvent):
    pass


@dataclass
class MeetingReady(MeetingEvent):
    pass


@dataclass
class MeetingSubmitted(MeetingEvent):
    workflow_id: str = ""


@dataclass
class MeetingCompleted(MeetingEvent):
    result: str = ""


@dataclass
class MeetingCancelled(MeetingEvent):
    reason: str = ""


@dataclass
class MeetingFailed(MeetingEvent):
    error: str = ""
    recoverable: bool = False


@dataclass
class MeetingArchived(MeetingEvent):
    reason: str = ""
