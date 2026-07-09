from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any


@dataclass
class MeetingPolicies:
    required_fields: list[str] = field(default_factory=lambda: [
        "attendee",
        "date",
        "time",
        "duration",
        "meeting_type",
        "title",
    ])
    optional_fields: list[str] = field(default_factory=lambda: [
        "agenda",
        "location",
        "organizer",
        "priority",
        "timezone",
        "description",
    ])
    field_collection_order: list[str] = field(default_factory=lambda: [
        "title",
        "attendee",
        "date",
        "time",
        "duration",
        "timezone",
        "meeting_type",
        "location",
        "agenda",
        "organizer",
        "priority",
        "description",
    ])
    max_collection_rounds: int = 20
    confirmation_timeout: timedelta = timedelta(minutes=30)
    allow_partial_confirmation: bool = True
    allow_field_correction: bool = True
    allow_reschedule: bool = True
    allow_cancellation: bool = True
    max_reschedules: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_required(self, field_name: str) -> bool:
        return field_name in self.required_fields

    def is_optional(self, field_name: str) -> bool:
        return field_name in self.optional_fields

    def get_collection_order(self) -> list[str]:
        all_fields = list(dict.fromkeys(self.field_collection_order))
        return [f for f in all_fields if f in self.required_fields or f in self.optional_fields]


default_meeting_policies = MeetingPolicies()
