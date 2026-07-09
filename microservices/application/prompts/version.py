from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PromptVersion:
    version: str = "1.0.0"
    content: str = ""
    content_hash: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    changelog: str = ""
    author: str = "platform"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
            "changelog": self.changelog,
            "author": self.author,
        }
