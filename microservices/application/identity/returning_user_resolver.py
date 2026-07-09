from domain.enums.user_type import UserType
from domain.models.user import UserProfile


class ReturningUserResolver:
    async def resolve_by_email(self, email: str) -> UserProfile | None:
        return None

    async def resolve_by_phone(self, phone: str) -> UserProfile | None:
        return None

    async def resolve_by_session(self, session_id: str) -> UserProfile | None:
        return None

    async def resolve_returning_user(
        self,
        email: str | None = None,
        phone: str | None = None,
        session_id: str | None = None,
    ) -> UserProfile | None:
        if email:
            user = await self.resolve_by_email(email)
            if user:
                return user
        if phone:
            user = await self.resolve_by_phone(phone)
            if user:
                return user
        if session_id:
            user = await self.resolve_by_session(session_id)
            if user:
                return user
        return None

    async def classify_user_type(self, email: str | None = None, domain: str | None = None) -> UserType:
        return UserType.VISITOR
