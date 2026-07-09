from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.knowledge.value_objects import ChunkingStrategy


@dataclass
class KnowledgeEvent:
    document_id: str = ""
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeCreated(KnowledgeEvent):
    title: str = ""
    doc_type: str = ""


@dataclass
class KnowledgeUploaded(KnowledgeEvent):
    pass


@dataclass
class KnowledgeProcessingStarted(KnowledgeEvent):
    pass


@dataclass
class KnowledgeChunked(KnowledgeEvent):
    chunk_count: int = 0
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE


@dataclass
class KnowledgeEmbeddingStarted(KnowledgeEvent):
    pass


@dataclass
class KnowledgeEmbedded(KnowledgeEvent):
    chunk_count: int = 0


@dataclass
class KnowledgeIndexed(KnowledgeEvent):
    pass


@dataclass
class KnowledgeActivated(KnowledgeEvent):
    pass


@dataclass
class KnowledgeArchived(KnowledgeEvent):
    reason: str = ""


@dataclass
class KnowledgeDeleted(KnowledgeEvent):
    reason: str = ""


@dataclass
class KnowledgeChunkAdded(KnowledgeEvent):
    chunk_id: str = ""
    chunk_index: int = 0


@dataclass
class KnowledgeChunkRemoved(KnowledgeEvent):
    chunk_id: str = ""


@dataclass
class KnowledgeVersionChanged(KnowledgeEvent):
    old_version: str = ""
    new_version: str = ""


@dataclass
class KnowledgeError(KnowledgeEvent):
    error: str = ""
