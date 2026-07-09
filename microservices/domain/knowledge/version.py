from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from domain.knowledge.value_objects import KnowledgeVersion


@dataclass
class KnowledgeVersionInfo:
    document_version: KnowledgeVersion = field(default_factory=KnowledgeVersion)
    embedding_version: KnowledgeVersion = field(default_factory=KnowledgeVersion)
    chunk_version: KnowledgeVersion = field(default_factory=KnowledgeVersion)
    source_version: str = ""
    change_detected_at: datetime | None = None
    incremental_update: bool = False
    changes: list[str] = field(default_factory=list)
