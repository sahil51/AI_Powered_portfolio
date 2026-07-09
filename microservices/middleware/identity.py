import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from application.identity.context import IdentityContext, set_identity_context
from application.identity.service import IdentityService

identity_service = IdentityService()


class IdentityResolutionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        email = request.headers.get("X-Email")
        phone = request.headers.get("X-Phone")
        session_id = request.headers.get("X-Session-ID")
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        request.state.correlation_id = correlation_id

        result = await identity_service.resolve_identity(
            auth_header=auth_header,
            email=email,
            phone=phone,
            session_id=session_id,
        )

        if not result.session_id:
            session_id = await identity_service.get_or_create_session(session_id)
        else:
            session_id = result.session_id

        ctx = IdentityContext(
            user_id=result.user_id,
            email=result.email,
            phone=result.phone,
            session_id=session_id,
            identity_source=result.identity_source.value,
            correlation_id=correlation_id,
        )
        set_identity_context(ctx)

        request.state.user_id = result.user_id
        request.state.email = result.email
        request.state.identity_source = result.identity_source.value
        request.state.session_id = session_id
        request.state.identity_ctx = ctx

        response: Response = await call_next(request)

        if result.identity_source.value in ("anonymous", "session"):
            response.headers["X-Session-ID"] = session_id

        response.headers["X-Identity-Source"] = result.identity_source.value

        return response
