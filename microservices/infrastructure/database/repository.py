from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.interfaces.repository import IRepository
from infrastructure.database.base import BaseEntity
from infrastructure.database.exceptions import RepositoryError

ModelT = TypeVar("ModelT", bound=BaseEntity)


class GenericRepository(IRepository[ModelT], Generic[ModelT]):
    def __init__(self, session: AsyncSession, model_class: type[ModelT]) -> None:
        self._session = session
        self._model = model_class

    def _stmt_base(self) -> Select:
        return select(self._model)

    def _apply_sorting(self, stmt: Select, sort_by: str | None, sort_desc: bool) -> Select:
        if sort_by is None or not hasattr(self._model, sort_by):
            return stmt
        column = getattr(self._model, sort_by)
        return stmt.order_by(desc(column) if sort_desc else column)

    def _apply_pagination(self, stmt: Select, skip: int, limit: int) -> Select:
        return stmt.offset(skip).limit(limit)

    def _apply_soft_delete_filter(self, stmt: Select, include_deleted: bool = False) -> Select:
        if not include_deleted and hasattr(self._model, "is_deleted"):
            return stmt.where(self._model.is_deleted.is_(False))
        return stmt

    async def add(self, entity: ModelT) -> ModelT:
        try:
            self._session.add(entity)
            await self._session.flush()
            await self._session.refresh(entity)
            return entity
        except Exception as e:
            raise RepositoryError(message=f"Failed to add {self._model.__name__}", detail=str(e))

    async def add_many(self, entities: Sequence[ModelT]) -> Sequence[ModelT]:
        try:
            self._session.add_all(entities)
            await self._session.flush()
            for entity in entities:
                await self._session.refresh(entity)
            return entities
        except Exception as e:
            raise RepositoryError(message=f"Failed to add multiple {self._model.__name__}", detail=str(e))

    async def get(self, id: str, for_update: bool = False) -> ModelT | None:
        stmt = self._stmt_base().where(self._model.id == id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_desc: bool = False,
    ) -> tuple[Sequence[ModelT], int]:
        base = self._apply_soft_delete_filter(self._stmt_base())
        count_stmt = select(func.count()).select_from(base.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        query = self._apply_sorting(base, sort_by, sort_desc)
        query = self._apply_pagination(query, skip, limit)
        result = await self._session.execute(query)
        items = result.scalars().all()
        return items, total

    async def update(self, entity: ModelT) -> ModelT:
        try:
            await self._session.merge(entity)
            await self._session.flush()
            return entity
        except Exception as e:
            raise RepositoryError(message=f"Failed to update {self._model.__name__}", detail=str(e))

    async def delete(self, entity: ModelT) -> None:
        try:
            await self._session.delete(entity)
            await self._session.flush()
        except Exception as e:
            raise RepositoryError(message=f"Failed to delete {self._model.__name__}", detail=str(e))

    async def soft_delete(self, entity: ModelT) -> ModelT:
        if not hasattr(entity, "is_deleted") or entity.is_deleted is None:
            raise RepositoryError(message=f"{self._model.__name__} does not support soft delete")
        entity.is_deleted = True  # type: ignore[assignment]
        await self._session.flush()
        return entity

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self._model)
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def exists(self, id: str) -> bool:
        stmt = select(self._model).where(self._model.id == id)
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def find_by(self, **kwargs: Any) -> list[ModelT]:
        stmt = self._stmt_base()
        for key, value in kwargs.items():
            if hasattr(self._model, key):
                stmt = stmt.where(getattr(self._model, key) == value)
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_one_by(self, **kwargs: Any) -> ModelT | None:
        stmt = self._stmt_base()
        for key, value in kwargs.items():
            if hasattr(self._model, key):
                stmt = stmt.where(getattr(self._model, key) == value)
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_many(self, filters: dict[str, Any], values: dict[str, Any]) -> int:
        try:
            stmt = update(self._model).where(
                *[getattr(self._model, k) == v for k, v in filters.items()]
            ).values(**values)
            result = await self._session.execute(stmt)
            await self._session.flush()
            return result.rowcount
        except Exception as e:
            raise RepositoryError(message=f"Failed to bulk update {self._model.__name__}", detail=str(e))

    async def delete_many(self, filters: dict[str, Any]) -> int:
        try:
            from sqlalchemy import delete as delete_stmt

            stmt = delete_stmt(self._model).where(
                *[getattr(self._model, k) == v for k, v in filters.items()]
            )
            result = await self._session.execute(stmt)
            await self._session.flush()
            return result.rowcount
        except Exception as e:
            raise RepositoryError(message=f"Failed to bulk delete {self._model.__name__}", detail=str(e))
