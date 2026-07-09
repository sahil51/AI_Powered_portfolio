from application.identity.cache import IdentityCache
from application.identity.context import IdentityContext, set_identity_context
from application.identity.resolver import IdentityResolutionResult, IdentityResolver, IdentitySource
from application.identity.returning_user_resolver import ReturningUserResolver
from application.identity.session_manager import SessionManager
from application.identity.validator import IdentityValidator


class IdentityService:
    def __init__(
        self,
        resolver: IdentityResolver | None = None,
        validator: IdentityValidator | None = None,
        session_manager: SessionManager | None = None,
        returning_user_resolver: ReturningUserResolver | None = None,
        cache: IdentityCache | None = None,
    ) -> None:
        self._resolver = resolver or IdentityResolver()
        self._validator = validator or IdentityValidator()
        self._session_manager = session_manager or SessionManager()
        self._returning_user_resolver = returning_user_resolver or ReturningUserResolver()
        self._cache = cache or IdentityCache()

    async def resolve_identity(
        self,
        auth_header: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        session_id: str | None = None,
    ) -> IdentityResolutionResult:
        result = await self._resolver.resolve(
            auth_header=auth_header,
            email=email,
            phone=phone,
            session_id=session_id,
        )

        if result.resolved and result.identity_source == IdentitySource.JWT:
            await self._cache.cache_identity(result.user_id, {
                "email": result.email,
                "source": result.identity_source.value,
            })

        ctx = IdentityContext(
            user_id=result.user_id,
            email=result.email,
            phone=result.phone,
            session_id=result.session_id,
            identity_source=result.identity_source.value,
        )
        set_identity_context(ctx)

        return result

    async def get_or_create_session(self, session_id: str | None = None) -> str:
        return await self._session_manager.get_or_create(session_id)

    async def merge_identities(self, anonymous_id: str, authenticated_id: str) -> None:
        await self._cache.merge_identity_data(anonymous_id, authenticated_id)

    async def invalidate_identity(self, user_id: str) -> None:
        await self._cache.invalidate_identity(user_id)
