from collections.abc import Sequence
from typing import Protocol

from domain.memory.aggregate import Memory
from domain.memory.value_objects import MemoryCategory, MemoryId, MemoryScope


class MemoryRepository(Protocol):
    async def save(self, memory: Memory) -> None:
        ...

    async def get_by_id(self, memory_id: MemoryId) -> Memory | None:
        ...

    async def get_by_id_str(self, memory_id: str) -> Memory | None:
        ...

    async def get_by_user(
        self,
        user_id: str,
        category: MemoryCategory | None = None,
        scope: MemoryScope | None = None,
        limit: int = 50,
    ) -> Sequence[Memory]:
        ...

    async def get_by_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> Sequence[Memory]:
        ...

    async def get_by_key(self, user_id: str, key_namespace: str, key: str) -> Memory | None:
        ...

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        user_id: str | None = None,
        category: str | None = None,
        scope: str | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[Memory], int]:
        ...

    async def delete(self, memory_id: MemoryId) -> None:
        ...

    async def count_by_user(self, user_id: str, scope: MemoryScope | None = None) -> int:
        ...

    async def expire_old(self, retention_days: int = 365) -> list[Memory]:
        ...

    async def search_metadata(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
    ) -> Sequence[Memory]:
        ...
