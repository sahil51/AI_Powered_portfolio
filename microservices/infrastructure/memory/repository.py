from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import Select, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.memory.aggregate import Memory, MemoryRecord
from domain.memory.state import MemoryStateMachine, MemoryStatus
from domain.memory.value_objects import (
    MemoryCategory,
    MemoryConfidence,
    MemoryId,
    MemoryImportance,
    MemoryKey,
    MemoryPriority,
    MemoryScope,
    MemorySource,
)
from infrastructure.memory.models import MemoryDBModel, MemoryRecordDBModel


class SQLAlchemyMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, memory: Memory) -> None:
        existing = await self._session.get(MemoryDBModel, str(memory.memory_id))
        if existing:
            await self._update_model(existing, memory)
        else:
            model = self._to_model(memory)
            self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, memory_id: MemoryId) -> Memory | None:
        return await self.get_by_id_str(memory_id.value)

    async def get_by_id_str(self, memory_id: str) -> Memory | None:
        model = await self._session.get(MemoryDBModel, memory_id)
        if model is None or model.is_deleted:
            return None
        return await self._to_domain(model)

    async def get_by_user(
        self,
        user_id: str,
        category: MemoryCategory | None = None,
        scope: MemoryScope | None = None,
        limit: int = 50,
    ) -> Sequence[Memory]:
        stmt = self._stmt_base().where(MemoryDBModel.user_id == user_id)
        if category:
            stmt = stmt.where(MemoryDBModel.category == category.value)
        if scope:
            stmt = stmt.where(MemoryDBModel.scope == scope.value)
        stmt = stmt.order_by(MemoryDBModel.last_activity_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [await self._to_domain(m) for m in result.scalars().all()]

    async def get_by_conversation(self, conversation_id: str, limit: int = 50) -> Sequence[Memory]:
        stmt = (
            self._stmt_base()
            .where(MemoryDBModel.conversation_id == conversation_id)
            .order_by(MemoryDBModel.last_activity_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [await self._to_domain(m) for m in result.scalars().all()]

    async def get_by_key(self, user_id: str, key_namespace: str, key: str) -> Memory | None:
        stmt = self._stmt_base().where(
            MemoryDBModel.user_id == user_id,
            MemoryDBModel.key_namespace == key_namespace,
            MemoryDBModel.key_value == key,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return await self._to_domain(model)

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        user_id: str | None = None,
        category: str | None = None,
        scope: str | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[Memory], int]:
        query = self._stmt_base()
        count_query = select(func.count()).select_from(MemoryDBModel).where(MemoryDBModel.is_deleted.is_(False))

        if user_id:
            query = query.where(MemoryDBModel.user_id == user_id)
            count_query = count_query.where(MemoryDBModel.user_id == user_id)
        if category:
            query = query.where(MemoryDBModel.category == category)
            count_query = count_query.where(MemoryDBModel.category == category)
        if scope:
            query = query.where(MemoryDBModel.scope == scope)
            count_query = count_query.where(MemoryDBModel.scope == scope)
        if status:
            query = query.where(MemoryDBModel.status == status)
            count_query = count_query.where(MemoryDBModel.status == status)

        total = (await self._session.execute(count_query)).scalar_one()
        query = query.order_by(MemoryDBModel.last_activity_at.desc()).offset(skip).limit(limit)
        models = (await self._session.execute(query)).scalars().all()
        return [await self._to_domain(m) for m in models], total

    async def delete(self, memory_id: MemoryId) -> None:
        model = await self._session.get(MemoryDBModel, memory_id.value)
        if model:
            model.is_deleted = True
            await self._session.flush()

    async def count_by_user(self, user_id: str, scope: MemoryScope | None = None) -> int:
        stmt = select(func.count()).select_from(MemoryDBModel).where(
            MemoryDBModel.user_id == user_id, MemoryDBModel.is_deleted.is_(False),
        )
        if scope:
            stmt = stmt.where(MemoryDBModel.scope == scope.value)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def expire_old(self, retention_days: int = 365) -> list[Memory]:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        stmt = (
            select(MemoryDBModel)
            .where(MemoryDBModel.status.in_(["active", "updated", "merged"]))
            .where(MemoryDBModel.last_activity_at < cutoff)
            .where(MemoryDBModel.is_deleted.is_(False))
        )
        models = (await self._session.execute(stmt)).scalars().all()
        if models:
            update_stmt = (
                update(MemoryDBModel)
                .where(MemoryDBModel.id.in_([m.id for m in models]))
                .values(status=MemoryStatus.EXPIRED.value)
            )
            await self._session.execute(update_stmt)
            await self._session.flush()
        return [await self._to_domain(m) for m in models]

    async def search_metadata(self, user_id: str, query: str, limit: int = 20) -> Sequence[Memory]:
        pattern = f"%{query}%"
        stmt = (
            self._stmt_base()
            .where(MemoryDBModel.user_id == user_id)
            .where(
                or_(
                    MemoryDBModel.value.ilike(pattern),
                    MemoryDBModel.category.ilike(pattern),
                    MemoryDBModel.scope.ilike(pattern),
                    MemoryDBModel.memory_type.ilike(pattern),
                )
            )
            .order_by(MemoryDBModel.importance, MemoryDBModel.confidence, MemoryDBModel.last_activity_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [await self._to_domain(m) for m in result.scalars().all()]

    async def count_all(self, user_id: str | None = None) -> int:
        stmt = select(func.count()).select_from(MemoryDBModel).where(MemoryDBModel.is_deleted.is_(False))
        if user_id:
            stmt = stmt.where(MemoryDBModel.user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one()

    async def count_by_status(self, user_id: str | None = None) -> dict[str, int]:
        stmt = select(MemoryDBModel.status, func.count()).where(MemoryDBModel.is_deleted.is_(False))
        if user_id:
            stmt = stmt.where(MemoryDBModel.user_id == user_id)
        stmt = stmt.group_by(MemoryDBModel.status)
        return dict((await self._session.execute(stmt)).all())

    async def count_by_category(self, user_id: str | None = None) -> dict[str, int]:
        stmt = select(MemoryDBModel.category, func.count()).where(MemoryDBModel.is_deleted.is_(False))
        if user_id:
            stmt = stmt.where(MemoryDBModel.user_id == user_id)
        stmt = stmt.group_by(MemoryDBModel.category)
        return dict((await self._session.execute(stmt)).all())

    async def search_advanced(
        self,
        user_id: str | None = None,
        conversation_id: str | None = None,
        session_id: str | None = None,
        category: str | None = None,
        scope: str | None = None,
        priority: str | None = None,
        confidence: str | None = None,
        importance: str | None = None,
        source: str | None = None,
        status: str | None = None,
        tags: list[str] | None = None,
        query: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "last_activity_at",
        sort_desc: bool = True,
    ) -> tuple[Sequence[Memory], int]:
        base = self._stmt_base()
        count_base = select(func.count()).select_from(MemoryDBModel).where(MemoryDBModel.is_deleted.is_(False))

        if user_id:
            base = base.where(MemoryDBModel.user_id == user_id)
            count_base = count_base.where(MemoryDBModel.user_id == user_id)
        if conversation_id:
            base = base.where(MemoryDBModel.conversation_id == conversation_id)
            count_base = count_base.where(MemoryDBModel.conversation_id == conversation_id)
        if session_id:
            base = base.where(MemoryDBModel.session_id == session_id)
            count_base = count_base.where(MemoryDBModel.session_id == session_id)
        if category:
            base = base.where(MemoryDBModel.category == category)
            count_base = count_base.where(MemoryDBModel.category == category)
        if scope:
            base = base.where(MemoryDBModel.scope == scope)
            count_base = count_base.where(MemoryDBModel.scope == scope)
        if priority:
            base = base.where(MemoryDBModel.priority == priority)
            count_base = count_base.where(MemoryDBModel.priority == priority)
        if confidence:
            base = base.where(MemoryDBModel.confidence == confidence)
            count_base = count_base.where(MemoryDBModel.confidence == confidence)
        if importance:
            base = base.where(MemoryDBModel.importance == importance)
            count_base = count_base.where(MemoryDBModel.importance == importance)
        if source:
            base = base.where(MemoryDBModel.source == source)
            count_base = count_base.where(MemoryDBModel.source == source)
        if status:
            base = base.where(MemoryDBModel.status == status)
            count_base = count_base.where(MemoryDBModel.status == status)
        if tags:
            for tag in tags:
                base = base.where(MemoryDBModel.tags.any(tag))
                count_base = count_base.where(MemoryDBModel.tags.any(tag))
        if query:
            pattern = f"%{query}%"
            base = base.where(MemoryDBModel.value.ilike(pattern))
            count_base = count_base.where(MemoryDBModel.value.ilike(pattern))
        if date_from:
            base = base.where(MemoryDBModel.created_at >= date_from)
            count_base = count_base.where(MemoryDBModel.created_at >= date_from)
        if date_to:
            base = base.where(MemoryDBModel.created_at <= date_to)
            count_base = count_base.where(MemoryDBModel.created_at <= date_to)

        total = (await self._session.execute(count_base)).scalar_one()

        sort_column = getattr(MemoryDBModel, sort_by, MemoryDBModel.last_activity_at)
        order_fn = desc if sort_desc else lambda c: c
        base = base.order_by(order_fn(sort_column)).offset(skip).limit(limit)

        models = (await self._session.execute(base)).scalars().all()
        return [await self._to_domain(m) for m in models], total

    @staticmethod
    def _stmt_base() -> Select:
        return select(MemoryDBModel).where(MemoryDBModel.is_deleted.is_(False))

    def _to_model(self, domain: Memory) -> MemoryDBModel:
        return MemoryDBModel(
            id=str(domain.memory_id),
            user_id=domain.user_id,
            conversation_id=domain.conversation_id,
            session_id=domain.session_id,
            key_namespace=domain.key.namespace if domain.key else None,
            key_value=domain.key.key if domain.key else None,
            value=domain.value,
            memory_type=domain.memory_type,
            category=domain.category.value,
            scope=domain.scope.value,
            priority=domain.priority.value,
            confidence=domain.confidence.value,
            importance=domain.importance.value,
            source=domain.source.value,
            status=domain.status.value,
            tags=domain.tags,
            metadata_=domain.metadata,
            correlation_id=domain.correlation_id,
            expires_at=domain.expires_at,
            last_activity_at=domain.updated_at,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            version=domain.version,
        )

    async def _update_model(self, model: MemoryDBModel, domain: Memory) -> None:
        model.user_id = domain.user_id
        model.conversation_id = domain.conversation_id
        model.session_id = domain.session_id
        model.key_namespace = domain.key.namespace if domain.key else None
        model.key_value = domain.key.key if domain.key else None
        model.value = domain.value
        model.memory_type = domain.memory_type
        model.category = domain.category.value
        model.scope = domain.scope.value
        model.priority = domain.priority.value
        model.confidence = domain.confidence.value
        model.importance = domain.importance.value
        model.source = domain.source.value
        model.status = domain.status.value
        model.tags = domain.tags
        model.metadata_ = domain.metadata
        model.correlation_id = domain.correlation_id
        model.expires_at = domain.expires_at
        model.updated_at = domain.updated_at
        model.version = domain.version
        await self._sync_records(model, domain)

    async def _sync_records(self, model: MemoryDBModel, domain: Memory) -> None:
        existing_ids = {str(r.id) for r in model.records}
        domain_ids = {str(r.memory_id) for r in domain.records}
        for rid in existing_ids - domain_ids:
            rec = next(r for r in model.records if str(r.id) == rid)
            await self._session.delete(rec)
        for rec in domain.records:
            rid = str(rec.memory_id)
            if rid in existing_ids:
                db_rec = next(r for r in model.records if str(r.id) == rid)
                db_rec.value = rec.value
                db_rec.record_type = rec.memory_type
                db_rec.tags = rec.tags
                db_rec.metadata_ = rec.metadata
            else:
                db_rec = MemoryRecordDBModel(
                    id=rid,
                    memory_id=str(domain.memory_id),
                    value=rec.value,
                    record_type=rec.memory_type,
                    tags=rec.tags,
                    metadata_=rec.metadata,
                )
                self._session.add(db_rec)

    async def _to_domain(self, model: MemoryDBModel) -> Memory:

        key = MemoryKey(namespace=model.key_namespace, key=model.key_value) if model.key_namespace else None
        mid = MemoryId()
        object.__setattr__(mid, "value", str(model.id))

        memory = Memory(
            memory_id=mid,
            user_id=model.user_id,
            conversation_id=model.conversation_id,
            session_id=model.session_id,
            key=key,
            value=model.value,
            memory_type=model.memory_type or "fact",
            category=MemoryCategory(model.category),
            scope=MemoryScope(model.scope),
            priority=MemoryPriority(model.priority or "medium"),
            confidence=MemoryConfidence(model.confidence or "medium"),
            importance=MemoryImportance(model.importance or "medium"),
            source=MemorySource(model.source or "system"),
            state_machine=MemoryStateMachine(MemoryStatus(model.status or "active")),
            tags=model.tags or [],
            metadata=model.metadata_ or {},
            correlation_id=model.correlation_id,
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version or 1,
        )
        records = await self._load_records(model)
        memory.records = records
        return memory

    async def _load_records(self, model: MemoryDBModel) -> list[MemoryRecord]:
        stmt = (
            select(MemoryRecordDBModel)
            .where(MemoryRecordDBModel.memory_id == model.id)
            .where(MemoryRecordDBModel.is_deleted.is_(False))
            .order_by(MemoryRecordDBModel.created_at)
        )
        db_records = (await self._session.execute(stmt)).scalars().all()
        records: list[MemoryRecord] = []
        for r in db_records:
            rec = MemoryRecord(
                value=r.value,
                memory_type=r.record_type or "snapshot",
                tags=r.tags or [],
                metadata=r.metadata_ or {},
            )
            rid = MemoryId()
            object.__setattr__(rid, "value", str(r.id))
            object.__setattr__(rec, "memory_id", rid)
            records.append(rec)
        return records
