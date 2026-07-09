from abc import ABC
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from infrastructure.database.uow import UnitOfWork, unit_of_work


class BaseService(ABC):
    def __init__(self, uow: UnitOfWork | None = None) -> None:
        self._uow = uow

    @property
    def uow(self) -> UnitOfWork:
        if self._uow is None:
            raise RuntimeError("UnitOfWork not initialized")
        return self._uow

    @property
    def session(self):
        return self.uow.session

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[UnitOfWork]:
        async with unit_of_work() as uow:
            self._uow = uow
            try:
                yield uow
            finally:
                self._uow = None

    async def commit(self) -> None:
        await self.uow.commit()

    async def rollback(self) -> None:
        await self.uow.rollback()
