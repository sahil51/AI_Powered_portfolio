from __future__ import annotations

from typing import Any

from application.context_builder.interfaces import ContextLayer
from application.identity.context import IdentityContext, get_identity_context


class IdentityContextLayer(ContextLayer):
    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "identity"

    @property
    def priority(self) -> int:
        return 1

    async def build(self, **kwargs: Any) -> dict[str, Any]:
        ctx: IdentityContext | None = kwargs.get("identity_context")
        if ctx is None:
            try:
                ctx = get_identity_context()
            except LookupError:
                ctx = None

        if ctx is not None and ctx.user_id is not None:
            result = {
                "user_id": ctx.user_id,
                "email": ctx.email,
                "phone": ctx.phone if ctx.phone else "",
                "session_id": ctx.session_id,
                "source": ctx.identity_source,
                "correlation_id": ctx.correlation_id,
            }
        else:
            result = {
                "user_id": None,
                "email": None,
                "phone": "",
                "session_id": None,
                "source": "unknown",
                "correlation_id": None,
            }

        if "user_id" in kwargs:
            result["user_id"] = kwargs["user_id"]
        if "session_id" in kwargs:
            result["session_id"] = kwargs["session_id"]
        if "identity_source" in kwargs:
            result["source"] = kwargs["identity_source"]

        return result

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
