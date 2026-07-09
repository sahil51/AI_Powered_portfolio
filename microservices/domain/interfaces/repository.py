from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    @abstractmethod
    async def add(self, entity: T) -> T:
        ...

    @abstractmethod
    async def add_many(self, entities: Sequence[T]) -> Sequence[T]:
        ...

    @abstractmethod
    async def get(self, id: str, for_update: bool = False) -> T | None:
        ...

    @abstractmethod
    async def get_many(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_desc: bool = False,
    ) -> tuple[Sequence[T], int]:
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        ...

    @abstractmethod
    async def delete(self, entity: T) -> None:
        ...

    @abstractmethod
    async def soft_delete(self, entity: T) -> T:
        ...

    @abstractmethod
    async def count(self) -> int:
        ...

    @abstractmethod
    async def exists(self, id: str) -> bool:
        ...
