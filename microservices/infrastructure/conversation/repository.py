from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.conversation.aggregate import Conversation
from domain.conversation.state import ConversationState, ConversationStateMachine
from domain.conversation.value_objects import (
    Attachment,
    ConversationId,
    ConversationMetadata,
    Message,
    MessageId,
    MessageType,
    Participant,
    ParticipantId,
    ParticipantRole,
)
from infrastructure.conversation.models import ConversationDBModel, MessageDBModel, ParticipantDBModel


class SQLAlchemyConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, conversation: Conversation) -> None:
        existing = await self._session.get(ConversationDBModel, str(conversation.conversation_id))
        if existing:
            await self._update_model(existing, conversation)
        else:
            model = self._to_model(conversation)
            self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, conversation_id: ConversationId) -> Conversation | None:
        return await self.get_by_id_str(conversation_id.value)

    async def get_by_id_str(self, conversation_id: str) -> Conversation | None:
        model = await self._session.get(ConversationDBModel, conversation_id)
        if model is None:
            return None
        return await self._to_domain(model)

    async def get_active_by_user(self, user_id: str, limit: int = 10) -> Sequence[Conversation]:
        stmt = (
            select(ConversationDBModel)
            .where(ConversationDBModel.user_id == user_id)
            .where(ConversationDBModel.is_deleted.is_(False))
            .where(ConversationDBModel.state.in_([
                ConversationState.ACTIVE.value,
                ConversationState.COLLECTING_INFORMATION.value,
                ConversationState.WAITING_CONFIRMATION.value,
                ConversationState.WAITING_EXTERNAL_WORKFLOW.value,
                ConversationState.RESUMED.value,
            ]))
            .order_by(ConversationDBModel.last_activity_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [await self._to_domain(m) for m in models]

    async def get_by_session(self, session_id: str, limit: int = 10) -> Sequence[Conversation]:
        stmt = (
            select(ConversationDBModel)
            .where(ConversationDBModel.session_id == session_id)
            .where(ConversationDBModel.is_deleted.is_(False))
            .order_by(ConversationDBModel.last_activity_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [await self._to_domain(m) for m in models]

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        user_id: str | None = None,
        state: str | None = None,
        session_id: str | None = None,
    ) -> tuple[Sequence[Conversation], int]:
        query = select(ConversationDBModel).where(ConversationDBModel.is_deleted.is_(False))
        count_query = (
            select(func.count())
            .select_from(ConversationDBModel)
            .where(ConversationDBModel.is_deleted.is_(False))
        )

        if user_id:
            query = query.where(ConversationDBModel.user_id == user_id)
            count_query = count_query.where(ConversationDBModel.user_id == user_id)
        if state:
            query = query.where(ConversationDBModel.state == state)
            count_query = count_query.where(ConversationDBModel.state == state)
        if session_id:
            query = query.where(ConversationDBModel.session_id == session_id)
            count_query = count_query.where(ConversationDBModel.session_id == session_id)

        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        query = query.order_by(ConversationDBModel.last_activity_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        models = result.scalars().all()

        domains = [await self._to_domain(m) for m in models]
        return domains, total

    async def delete(self, conversation_id: ConversationId) -> None:
        model = await self._session.get(ConversationDBModel, conversation_id.value)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def count_active_by_user(self, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ConversationDBModel)
            .where(ConversationDBModel.user_id == user_id)
            .where(ConversationDBModel.is_deleted.is_(False))
            .where(ConversationDBModel.state.in_([
                ConversationState.ACTIVE.value,
                ConversationState.COLLECTING_INFORMATION.value,
                ConversationState.WAITING_CONFIRMATION.value,
                ConversationState.WAITING_EXTERNAL_WORKFLOW.value,
                ConversationState.RESUMED.value,
            ]))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def archive_old(self, before_days: int = 90) -> int:
        from sqlalchemy import update
        stmt = (
            update(ConversationDBModel)
            .where(ConversationDBModel.state.in_([
                ConversationState.COMPLETED.value,
                ConversationState.CANCELLED.value,
            ]))
            .where(ConversationDBModel.updated_at < datetime.now(timezone.utc))
            .values(state=ConversationState.ARCHIVED.value)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount

    async def expire_idle(self, timeout_minutes: int = 30) -> list[Conversation]:
        from datetime import timedelta

        from sqlalchemy import update

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        stmt = (
            select(ConversationDBModel)
            .where(ConversationDBModel.state.in_([
                ConversationState.ACTIVE.value,
                ConversationState.COLLECTING_INFORMATION.value,
                ConversationState.WAITING_CONFIRMATION.value,
                ConversationState.WAITING_EXTERNAL_WORKFLOW.value,
                ConversationState.RESUMED.value,
            ]))
            .where(ConversationDBModel.last_activity_at < cutoff)
            .where(ConversationDBModel.is_deleted.is_(False))
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        if models:
            update_stmt = (
                update(ConversationDBModel)
                .where(ConversationDBModel.id.in_([m.id for m in models]))
                .values(state=ConversationState.CANCELLED.value)
            )
            await self._session.execute(update_stmt)
            await self._session.flush()

        return [await self._to_domain(m) for m in models]

    def _to_model(self, domain: Conversation) -> ConversationDBModel:
        return ConversationDBModel(
            id=str(domain.conversation_id),
            user_id=domain.user_id,
            session_id=domain.session_id,
            identity_source=domain.identity_source,
            state=domain.state.value,
            summary=domain.summary,
            correlation_id=domain.correlation_id,
            paused_at=domain.paused_at,
            completed_at=domain.completed_at,
            last_activity_at=domain.last_activity_at,
            title=domain.metadata.title,
            description=domain.metadata.description,
            tags=domain.metadata.tags,
            source=domain.metadata.source,
            language=domain.metadata.language,
            timezone=domain.metadata.timezone,
            custom_fields=domain.metadata.custom_fields,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            version=domain.version,
        )

    async def _update_model(self, model: ConversationDBModel, domain: Conversation) -> None:
        model.user_id = domain.user_id
        model.session_id = domain.session_id
        model.identity_source = domain.identity_source
        model.state = domain.state.value
        model.summary = domain.summary
        model.correlation_id = domain.correlation_id
        model.paused_at = domain.paused_at
        model.completed_at = domain.completed_at
        model.last_activity_at = domain.last_activity_at
        model.title = domain.metadata.title
        model.description = domain.metadata.description
        model.tags = domain.metadata.tags
        model.source = domain.metadata.source
        model.language = domain.metadata.language
        model.timezone = domain.metadata.timezone
        model.custom_fields = domain.metadata.custom_fields
        model.updated_at = domain.updated_at
        model.version = domain.version

        await self._sync_messages(model, domain)
        await self._sync_participants(model, domain)

    async def _sync_messages(self, model: ConversationDBModel, domain: Conversation) -> None:
        existing_ids = {str(m.id) for m in model.messages}
        domain_ids = {str(m.message_id) for m in domain.messages}

        for msg_id in existing_ids - domain_ids:
            await self._session.delete(next(m for m in model.messages if str(m.id) == msg_id))

        for msg in domain.messages:
            msg_id = str(msg.message_id)
            if msg_id in existing_ids:
                db_msg = next(m for m in model.messages if str(m.id) == msg_id)
                db_msg.content = msg.content
                db_msg.message_type = msg.message_type.value
                db_msg.token_count = msg.token_count
                db_msg.metadata_ = msg.metadata
                db_msg.attachments = [{"filename": a.filename, "content_type": a.content_type,
                                        "size_bytes": a.size_bytes, "storage_path": a.storage_path}
                                       for a in msg.attachments]
            else:
                db_msg = MessageDBModel(
                    id=msg_id,
                    conversation_id=str(domain.conversation_id),
                    message_type=msg.message_type.value,
                    content=msg.content,
                    participant_id=str(msg.participant_id) if msg.participant_id else None,
                    correlation_id=msg.correlation_id,
                    token_count=msg.token_count,
                    metadata_=msg.metadata,
                    attachments=[{"filename": a.filename, "content_type": a.content_type,
                                   "size_bytes": a.size_bytes, "storage_path": a.storage_path}
                                  for a in msg.attachments],
                    created_at=msg.created_at,
                )
                self._session.add(db_msg)

    async def _sync_participants(self, model: ConversationDBModel, domain: Conversation) -> None:
        existing_ids = {str(m.participant_id) for m in model.participants}
        domain_ids = {str(m.participant_id) for m in domain.participants}

        for pid in existing_ids - domain_ids:
            await self._session.delete(next(m for m in model.participants if str(m.participant_id) == pid))

        for participant in domain.participants:
            pid = str(participant.participant_id)
            if pid in existing_ids:
                db_p = next(m for m in model.participants if str(m.participant_id) == pid)
                db_p.role = participant.role.value
                db_p.left_at = participant.left_at
                db_p.metadata_ = participant.metadata
            else:
                db_p = ParticipantDBModel(
                    conversation_id=str(domain.conversation_id),
                    participant_id=pid,
                    role=participant.role.value,
                    joined_at=participant.joined_at,
                    left_at=participant.left_at,
                    metadata_=participant.metadata,
                )
                self._session.add(db_p)

    async def _to_domain(self, model: ConversationDBModel) -> Conversation:
        messages = await self._load_messages(model)
        participants = self._load_participants(model)

        conv = Conversation(
            conversation_id=ConversationId(),
            user_id=model.user_id,
            session_id=model.session_id or "",
            identity_source=model.identity_source or "anonymous",
            state_machine=ConversationStateMachine(ConversationState(model.state)),
            metadata=ConversationMetadata(
                title=model.title,
                description=model.description,
                tags=model.tags or [],
                source=model.source or "chat",
                timezone=model.timezone or "UTC",
                language=model.language or "en",
                custom_fields=model.custom_fields or {},
            ),
            summary=model.summary,
            correlation_id=model.correlation_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_activity_at=model.last_activity_at,
            paused_at=model.paused_at,
            completed_at=model.completed_at,
            version=model.version or 1,
        )
        conv.conversation_id = ConversationId()
        conv.conversation_id.value = str(model.id)
        conv.messages = messages
        conv.participants = participants
        return conv

    async def _load_messages(self, model: ConversationDBModel) -> list[Message]:
        stmt = (
            select(MessageDBModel)
            .where(MessageDBModel.conversation_id == model.id)
            .order_by(MessageDBModel.created_at)
        )
        result = await self._session.execute(stmt)
        db_messages = result.scalars().all()
        messages: list[Message] = []
        for db_msg in db_messages:
            attachments = []
            if db_msg.attachments:
                for a in db_msg.attachments:
                    attachments.append(Attachment(
                        filename=a.get("filename", ""),
                        content_type=a.get("content_type", ""),
                        size_bytes=a.get("size_bytes", 0),
                        storage_path=a.get("storage_path"),
                    ))
            msg = Message(
                message_id=MessageId(),
                message_type=MessageType(db_msg.message_type),
                content=db_msg.content,
                participant_id=ParticipantId(value=db_msg.participant_id) if db_msg.participant_id else None,
                correlation_id=db_msg.correlation_id,
                token_count=db_msg.token_count or 0,
                metadata=db_msg.metadata_ or {},
                attachments=attachments,
                created_at=db_msg.created_at,
            )
            msg.message_id = MessageId()
            msg.message_id.value = str(db_msg.id)
            messages.append(msg)
        return messages

    def _load_participants(self, model: ConversationDBModel) -> list[Participant]:
        participants: list[Participant] = []
        for db_p in model.participants:
            participant = Participant(
                participant_id=ParticipantId(value=db_p.participant_id),
                role=ParticipantRole(db_p.role),
                joined_at=db_p.joined_at,
                left_at=db_p.left_at,
                metadata=db_p.metadata_ or {},
            )
            participants.append(participant)
        return participants
