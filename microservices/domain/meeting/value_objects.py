from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MeetingStatus(str, Enum):
    CREATED = "created"
    COLLECTING_INFORMATION = "collecting_information"
    WAITING_CONFIRMATION = "waiting_confirmation"
    READY = "ready"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    ARCHIVED = "archived"


class MeetingFieldStatus(str, Enum):
    PENDING = "pending"
    COLLECTED = "collected"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"


@dataclass(frozen=True)
class MeetingId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MeetingId):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass
class MeetingField:
    name: str
    value: str | None = None
    status: MeetingFieldStatus = MeetingFieldStatus.PENDING
    required: bool = True
    order: int = 0
    label: str = ""
    validation_error: str | None = None

    @property
    def is_collected(self) -> bool:
        return self.status in (MeetingFieldStatus.COLLECTED, MeetingFieldStatus.CONFIRMED, MeetingFieldStatus.CORRECTED)


@dataclass
class MeetingSession:
    session_id: str = ""
    meeting_id: str = ""
    user_id: str = ""
    status: MeetingStatus = MeetingStatus.CREATED
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MeetingMetadata:
    display_name: str = ""
    description: str = ""
    author: str = ""
    tags: tuple[str, ...] = ()
    custom: dict[str, str] = field(default_factory=dict)
