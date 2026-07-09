from __future__ import annotations

from application.meeting.exceptions import MeetingValidationError
from application.meeting.models import MeetingContext, MeetingResult


class MeetingApplicationValidator:
    def validate_context(self, context: MeetingContext) -> None:
        if not context:
            raise MeetingValidationError("Meeting context is required")
        if not context.user_id:
            raise MeetingValidationError("User ID is required")
        if not context.conversation_id:
            raise MeetingValidationError("Conversation ID is required")

    def validate_result(self, result: MeetingResult) -> bool:
        if not result.meeting_id:
            raise MeetingValidationError("Meeting ID is required in result")
        return True
