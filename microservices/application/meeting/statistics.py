from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.meeting.value_objects import MeetingStatus


@dataclass
class MeetingStatistics:
    total_meetings: int = 0
    by_status: dict[str, int] = field(default_factory=dict)
    by_user: dict[str, int] = field(default_factory=dict)
    total_fields_collected: int = 0
    avg_fields_per_meeting: float = 0.0
    correction_count: int = 0
    reschedule_count: int = 0
    unique_users: set[str] = field(default_factory=set)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class MeetingApplicationStatistics:
    def __init__(self) -> None:
        self._data = MeetingStatistics()

    @property
    def data(self) -> MeetingStatistics:
        return self._data

    def record_meeting_created(self, user_id: str) -> None:
        self._data.total_meetings += 1
        self._data.by_status["created"] = self._data.by_status.get("created", 0) + 1
        self._data.by_user[user_id] = self._data.by_user.get(user_id, 0) + 1
        self._data.unique_users.add(user_id)
        self._data.last_updated = datetime.now(timezone.utc)

    def record_status_change(self, from_status: MeetingStatus, to_status: MeetingStatus) -> None:
        from_key = from_status.value
        to_key = to_status.value
        self._data.by_status[from_key] = max(self._data.by_status.get(from_key, 1) - 1, 0)
        self._data.by_status[to_key] = self._data.by_status.get(to_key, 0) + 1
        self._data.last_updated = datetime.now(timezone.utc)

    def record_field_collected(self) -> None:
        self._data.total_fields_collected += 1
        self._data.avg_fields_per_meeting = (
            self._data.total_fields_collected / max(self._data.total_meetings, 1)
        )

    def record_correction(self) -> None:
        self._data.correction_count += 1

    def record_reschedule(self) -> None:
        self._data.reschedule_count += 1

    def reset(self) -> None:
        self._data = MeetingStatistics()
