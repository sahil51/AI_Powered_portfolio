from dataclasses import dataclass

from domain.memory.value_objects import MemoryCategory, MemoryScope


@dataclass
class GetMemoryQuery:
    memory_id: str


@dataclass
class GetUserMemoriesQuery:
    user_id: str
    category: MemoryCategory | None = None
    scope: MemoryScope | None = None
    limit: int = 50


@dataclass
class SearchMemoriesQuery:
    user_id: str
    query: str
    limit: int = 20
