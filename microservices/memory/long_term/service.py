import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.user import UserProfile
from infrastructure.database.models import ConversationModel, UserModel


class LongTermMemory:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, email: str, name: Optional[str] = None, session_id: Optional[str] = None) -> UserProfile:
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        user = result.scalar_one_or_none()

        if user:
            if name and user.name != name:
                user.name = name
            if session_id and not user.session_id:
                user.session_id = session_id
            if name or (session_id and not user.session_id):
                await self.session.commit()
            return UserProfile(
                id=str(user.id),
                name=user.name,
                email=user.email,
                phone=user.phone,
                company=user.company,
                company_address=user.company_address,
                preferred_language=user.preferred_language,
                preferred_meeting_type=user.preferred_meeting_type,
                preferred_time=user.preferred_time,
                preferred_timezone=user.preferred_timezone,
                user_type=user.user_type,
            )

        new_user = UserModel(
            id=uuid.uuid4(),
            email=email,
            name=name,
            session_id=session_id,
        )
        self.session.add(new_user)
        await self.session.commit()
        return UserProfile(
            id=str(new_user.id),
            email=email,
            name=name,
        )

    async def get_or_create_session_user(self, session_id: str) -> UserProfile:
        result = await self.session.execute(select(UserModel).where(UserModel.session_id == session_id))
        user = result.scalar_one_or_none()

        if user:
            return UserProfile(
                id=str(user.id),
                name=user.name,
                email=user.email,
                phone=user.phone,
                company=user.company,
                company_address=user.company_address,
                preferred_language=user.preferred_language,
                preferred_meeting_type=user.preferred_meeting_type,
                preferred_time=user.preferred_time,
                preferred_timezone=user.preferred_timezone,
                user_type=user.user_type,
            )

        new_user = UserModel(
            id=uuid.uuid4(),
            session_id=session_id,
        )
        self.session.add(new_user)
        await self.session.commit()
        return UserProfile(
            id=str(new_user.id),
        )

    async def update_user_profile(self, user_id: str, updates: dict) -> None:
        try:
            user_uuid = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return
        stmt = update(UserModel).where(UserModel.id == user_uuid).values(**updates)
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        try:
            user_uuid = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return None
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_uuid))
        user = result.scalar_one_or_none()
        if user:
            return UserProfile(
                id=str(user.id),
                name=user.name,
                email=user.email,
                phone=user.phone,
                company=user.company,
                company_address=user.company_address,
                preferred_language=user.preferred_language,
                preferred_meeting_type=user.preferred_meeting_type,
                preferred_time=user.preferred_time,
                preferred_timezone=user.preferred_timezone,
                user_type=user.user_type,
            )
        return None

    async def save_conversation_summary(self, conversation_id: str, summary: str) -> None:
        try:
            conv_uuid = uuid.UUID(str(conversation_id))
        except (ValueError, TypeError):
            return
        stmt = update(ConversationModel).where(ConversationModel.id == conv_uuid).values(summary=summary)
        await self.session.execute(stmt)
        await self.session.commit()

