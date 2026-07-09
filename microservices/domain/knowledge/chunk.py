from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.knowledge.value_objects import ChunkId, EmbeddingStatus, KnowledgeVersion


@dataclass
class KnowledgeChunk:
    chunk_id: ChunkId = field(default_factory=ChunkId)
    document_id: str = ""
    chunk_index: int = 0
    text: str = ""
    token_count: int = 0
    character_count: int = 0
    section: str = ""
    heading: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    language: str = "en"
    version: KnowledgeVersion = field(default_factory=KnowledgeVersion)
    checksum: str = ""
    embedding_status: EmbeddingStatus = EmbeddingStatus.PENDING
    embedding: list[float] | None = None
    embedding_dimension: int = 0
    embedding_model: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_embedded(self) -> bool:
        return self.embedding_status == EmbeddingStatus.COMPLETED and self.embedding is not None

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()

    def is_oversized(self, max_tokens: int = 8191) -> bool:
        return self.token_count > max_tokens
