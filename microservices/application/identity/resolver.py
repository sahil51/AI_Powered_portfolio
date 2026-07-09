from dataclasses import dataclass, field
from enum import Enum

import jwt

from config.settings import settings
from monitoring.logger import logger


class IdentitySource(str, Enum):
    JWT = "jwt"
    EMAIL = "email"
    PHONE = "phone"
    SESSION = "session"
    ANONYMOUS = "anonymous"


@dataclass
class IdentityResolutionResult:
    user_id: str | None = None
    email: str | None = None
    phone: str | None = None
    session_id: str | None = None
    identity_source: IdentitySource = IdentitySource.ANONYMOUS
    jwt_payload: dict | None = None
    resolved: bool = False
    metadata: dict = field(default_factory=dict)


class IdentityResolver:
    def __init__(self) -> None:
        self._jwt_secret = settings.jwt_secret
        self._jwt_algorithm = settings.jwt_algorithm

    async def resolve(
        self,
        auth_header: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        session_id: str | None = None,
    ) -> IdentityResolutionResult:
        result = await self._resolve_jwt(auth_header)
        if result.resolved:
            return result

        result = await self._resolve_email(email)
        if result.resolved:
            return result

        result = await self._resolve_phone(phone)
        if result.resolved:
            return result

        result = await self._resolve_session(session_id)
        if result.resolved:
            return result

        return IdentityResolutionResult(
            identity_source=IdentitySource.ANONYMOUS,
            resolved=False,
        )

    async def _resolve_jwt(self, auth_header: str | None) -> IdentityResolutionResult:
        if not auth_header or not auth_header.startswith("Bearer "):
            return IdentityResolutionResult()

        token = auth_header.replace("Bearer ", "")
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            return IdentityResolutionResult(
                user_id=payload.get("sub"),
                email=payload.get("email"),
                session_id=payload.get("session_id"),
                identity_source=IdentitySource.JWT,
                jwt_payload=payload,
                resolved=True,
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token")
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
        return IdentityResolutionResult()

    async def _resolve_email(self, email: str | None) -> IdentityResolutionResult:
        if not email:
            return IdentityResolutionResult()
        return IdentityResolutionResult(
            user_id=email,
            email=email,
            identity_source=IdentitySource.EMAIL,
            resolved=True,
        )

    async def _resolve_phone(self, phone: str | None) -> IdentityResolutionResult:
        if not phone:
            return IdentityResolutionResult()
        return IdentityResolutionResult(
            user_id=phone,
            phone=phone,
            identity_source=IdentitySource.PHONE,
            resolved=True,
        )

    async def _resolve_session(self, session_id: str | None) -> IdentityResolutionResult:
        if not session_id:
            return IdentityResolutionResult()
        return IdentityResolutionResult(
            user_id=session_id,
            session_id=session_id,
            identity_source=IdentitySource.SESSION,
            resolved=True,
        )
