from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PromptStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class PromptVariable:
    name: str
    required: bool = True
    default: str | None = None
    description: str = ""


@dataclass
class PromptMetadata:
    name: str = ""
    category: str = ""
    version: str = "1.0.0"
    status: PromptStatus = PromptStatus.DRAFT
    description: str = ""
    tags: list[str] = field(default_factory=list)
    supported_models: list[str] = field(default_factory=list)
    variables: list[PromptVariable] = field(default_factory=list)
    owner: str = "platform"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deprecated_at: datetime | None = None
    content_hash: str = ""
    content_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "status": self.status.value,
            "description": self.description,
            "tags": list(self.tags),
            "supported_models": list(self.supported_models),
            "variables": [
                {"name": v.name, "required": v.required, "default": v.default, "description": v.description}
                for v in self.variables
            ],
            "owner": self.owner,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "content_hash": self.content_hash,
            "content_path": self.content_path,
        }
