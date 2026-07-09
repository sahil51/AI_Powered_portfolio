from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from application.context_builder.models import BuiltContext


@dataclass
class ContextSnapshot:
    context: BuiltContext | None = None
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def restore(self) -> BuiltContext | None:
        return self.context

    def is_expired(self, ttl_seconds: int = 300) -> bool:
        delta = (datetime.now(timezone.utc) - self.captured_at).total_seconds()
        return delta > ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "captured_at": self.captured_at.isoformat(),
            "label": self.label,
            "context": self.context.to_dict() if self.context else None,
            "metadata": self.metadata,
        }
