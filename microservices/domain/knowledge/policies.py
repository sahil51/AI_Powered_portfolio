from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from domain.knowledge.value_objects import ChunkingStrategy, DocumentType


@dataclass
class KnowledgePolicies:
    allowed_document_types: list[DocumentType] = field(default_factory=lambda: [
        DocumentType.PDF,
        DocumentType.DOCX,
        DocumentType.MARKDOWN,
        DocumentType.TXT,
        DocumentType.HTML,
        DocumentType.WEBSITE,
        DocumentType.FAQ,
        DocumentType.POLICY,
        DocumentType.MANUAL,
        DocumentType.KNOWLEDGE_ARTICLE,
        DocumentType.CUSTOM,
    ])
    max_chunk_size: int = 2000
    min_chunk_size: int = 100
    default_chunk_overlap: int = 200
    default_chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    max_document_size_bytes: int = 100 * 1024 * 1024
    max_chunks_per_document: int = 10000
    enable_compression: bool = False
    enable_deduplication: bool = True
    enable_versioning: bool = True
    auto_activate: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_allowed_type(self, doc_type: DocumentType) -> bool:
        return doc_type in self.allowed_document_types


default_knowledge_policies = KnowledgePolicies()
