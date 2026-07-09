import contextvars
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IdentityContext:
    user_id: str | None = None
    email: str | None = None
    phone: str | None = None
    session_id: str | None = None
    identity_source: str = "anonymous"
    correlation_id: str | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        return self.identity_source == "jwt"

    @property
    def is_anonymous(self) -> bool:
        return self.identity_source in ("anonymous", "session")

    @property
    def display_name(self) -> str:
        return self.email or self.user_id or self.session_id or "unknown"


_identity_context_var: contextvars.ContextVar[IdentityContext | None] = (
    contextvars.ContextVar("identity_context", default=None)
)


def get_identity_context() -> IdentityContext:
    ctx = _identity_context_var.get()
    if ctx is None:
        ctx = IdentityContext()
        _identity_context_var.set(ctx)
    return ctx


def set_identity_context(ctx: IdentityContext) -> None:
    _identity_context_var.set(ctx)


def reset_identity_context() -> None:
    _identity_context_var.set(None)


identity_context = get_identity_context
