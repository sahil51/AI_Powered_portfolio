from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from domain.knowledge.value_objects import DocumentId


@dataclass(frozen=True)
class KnowledgeIngestionEvent:
    document_id: DocumentId
    correlation_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeImported(KnowledgeIngestionEvent):
    source_type: str = ""
    file_name: str = ""


@dataclass(frozen=True)
class KnowledgeUpdated(KnowledgeIngestionEvent):
    old_version: str = ""
    new_version: str = ""


@dataclass(frozen=True)
class KnowledgeChunked(KnowledgeIngestionEvent):
    chunk_count: int = 0


@dataclass(frozen=True)
class KnowledgeEmbedded(KnowledgeIngestionEvent):
    chunk_count: int = 0


@dataclass(frozen=True)
class KnowledgeIndexed(KnowledgeIngestionEvent):
    chunk_count: int = 0


@dataclass(frozen=True)
class KnowledgeArchived(KnowledgeIngestionEvent):
    reason: str = ""


@dataclass(frozen=True)
class KnowledgeDeleted(KnowledgeIngestionEvent):
    reason: str = ""


@dataclass(frozen=True)
class KnowledgeImportFailed(KnowledgeIngestionEvent):
    error: str = ""
    stage: str = ""
