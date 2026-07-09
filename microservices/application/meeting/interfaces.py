from __future__ import annotations

from abc import ABC, abstractmethod

from application.meeting.models import MeetingContext, MeetingResult


class MeetingAgentInterface(ABC):
    @abstractmethod
    async def start_meeting(self, context: MeetingContext) -> MeetingResult:
        ...

    @abstractmethod
    async def process_message(self, meeting_id: str, message: str, context: MeetingContext) -> MeetingResult:
        ...

    @abstractmethod
    async def get_status(self, meeting_id: str) -> MeetingResult:
        ...

    @abstractmethod
    async def cancel_meeting(self, meeting_id: str, reason: str = "") -> MeetingResult:
        ...
