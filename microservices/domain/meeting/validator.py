from __future__ import annotations

from domain.meeting.aggregate import Meeting
from domain.meeting.policies import MeetingPolicies, default_meeting_policies
from domain.meeting.state import MeetingStatus


class MeetingValidationError(Exception):
    pass


class MeetingValidator:
    def __init__(self, policies: MeetingPolicies | None = None) -> None:
        self._policies = policies or default_meeting_policies

    def validate_create(self, title: str) -> None:
        if not title or not title.strip():
            raise MeetingValidationError("Meeting title is required")

    def validate_field_collection(self, meeting: Meeting) -> None:
        if not meeting.can_collect:
            raise MeetingValidationError(
                f"Cannot collect fields in state: {meeting.status.value}"
            )

    def validate_submit(self, meeting: Meeting) -> None:
        if meeting.status != MeetingStatus.READY:
            raise MeetingValidationError(
                f"Cannot submit meeting in state: {meeting.status.value}"
            )
        missing = [f.name for f in meeting.fields if f.required and not f.is_collected]
        if missing:
            raise MeetingValidationError(
                f"Cannot submit meeting with missing required fields: {', '.join(missing)}"
            )
