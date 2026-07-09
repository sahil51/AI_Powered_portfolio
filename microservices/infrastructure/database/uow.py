from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.exceptions import TransactionError
from infrastructure.database.session import db


class UnitOfWork:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session: AsyncSession | None = session
        self._nested = session is not None
        self._savepoint = None

    async def __aenter__(self) -> "UnitOfWork":
        if self._session is None:
            self._session = db.session_factory()
        if self._nested:
            self._savepoint = await self._session.begin_nested()  # type: ignore[assignment]
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._nested:
            if exc_type is not None and self._savepoint is not None:
                await self._savepoint.rollback()
            return

        try:
            if exc_type is None:
                await self._session.commit()  # type: ignore[union-attr]
            else:
                await self._session.rollback()  # type: ignore[union-attr]
        except Exception as e:
            raise TransactionError(message="UOW transaction failed", detail=str(e))
        finally:
            if self._session is not None:
                await self._session.close()

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise TransactionError(message="Session not initialized. Use 'async with UnitOfWork()'")
        return self._session

    async def commit(self) -> None:
        try:
            await self.session.commit()
        except Exception as e:
            raise TransactionError(message="Commit failed", detail=str(e))

    async def rollback(self) -> None:
        try:
            await self.session.rollback()
        except Exception as e:
            raise TransactionError(message="Rollback failed", detail=str(e))

    async def flush(self) -> None:
        try:
            await self.session.flush()
        except Exception as e:
            raise TransactionError(message="Flush failed", detail=str(e))


@asynccontextmanager
async def unit_of_work(session: AsyncSession | None = None) -> AsyncIterator[UnitOfWork]:
    async with UnitOfWork(session) as uow:
        yield uow
