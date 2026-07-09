from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from domain.meeting.aggregate import Meeting
from domain.meeting.value_objects import MeetingId, MeetingStatus


class MeetingRepository(Protocol):
    async def save(self, meeting: Meeting) -> None:
        ...

    async def get_by_id(self, meeting_id: MeetingId) -> Meeting | None:
        ...

    async def get_by_id_str(self, meeting_id: str) -> Meeting | None:
        ...

    async def get_by_user(self, user_id: str, limit: int = 50) -> Sequence[Meeting]:
        ...

    async def get_by_conversation(self, conversation_id: str) -> Meeting | None:
        ...

    async def get_by_status(self, status: MeetingStatus, limit: int = 50) -> Sequence[Meeting]:
        ...

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
        user_id: str | None = None,
    ) -> tuple[Sequence[Meeting], int]:
        ...

    async def delete(self, meeting_id: MeetingId) -> None:
        ...

    async def count_by_status(self, status: MeetingStatus) -> int:
        ...

    async def count_by_user(self, user_id: str) -> int:
        ...
