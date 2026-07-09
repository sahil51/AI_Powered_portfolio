from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from application.prompts.metadata import PromptMetadata, PromptStatus


@dataclass
class PromptManifest:
    version: str = "1.0"
    prompts: list[PromptMetadata] = field(default_factory=list)
    registry_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "registry_version": self.registry_version,
            "prompts": [p.to_dict() for p in self.prompts],
            "total_count": len(self.prompts),
            "active_count": len([p for p in self.prompts if p.status == PromptStatus.ACTIVE]),
        }
