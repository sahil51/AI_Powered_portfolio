from collections.abc import Sequence
from typing import Protocol

from domain.conversation.aggregate import Conversation
from domain.conversation.value_objects import ConversationId


class ConversationRepository(Protocol):
    async def save(self, conversation: Conversation) -> None:
        ...

    async def get_by_id(self, conversation_id: ConversationId) -> Conversation | None:
        ...

    async def get_by_id_str(self, conversation_id: str) -> Conversation | None:
        ...

    async def get_active_by_user(self, user_id: str, limit: int = 10) -> Sequence[Conversation]:
        ...

    async def get_by_session(self, session_id: str, limit: int = 10) -> Sequence[Conversation]:
        ...

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        user_id: str | None = None,
        state: str | None = None,
        session_id: str | None = None,
    ) -> tuple[Sequence[Conversation], int]:
        ...

    async def delete(self, conversation_id: ConversationId) -> None:
        ...

    async def count_active_by_user(self, user_id: str) -> int:
        ...

    async def archive_old(self, before_days: int = 90) -> int:
        ...

    async def expire_idle(self, timeout_minutes: int = 30) -> list[Conversation]:
        ...
