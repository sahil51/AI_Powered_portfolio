from dataclasses import dataclass, field
from typing import Any

from application.identity.context import IdentityContext


@dataclass
class ConversationContext:
    user_id: str = ""
    session_id: str | None = None
    identity_source: str = "anonymous"
    correlation_id: str | None = None
    workflow_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_identity_context(cls, identity: IdentityContext) -> "ConversationContext":
        return cls(
            user_id=identity.user_id or identity.session_id or "unknown",
            session_id=identity.session_id,
            identity_source=identity.identity_source,
            correlation_id=identity.correlation_id,
        )

    @classmethod
    def from_request(cls, request: object) -> "ConversationContext":
        req = request
        return cls(
            user_id=getattr(req.state, "user_id", None) or getattr(req.state, "session_id", "unknown"),
            session_id=getattr(req.state, "session_id", None),
            identity_source=getattr(req.state, "identity_source", "anonymous"),
            correlation_id=getattr(req.state, "correlation_id", None),
        )
