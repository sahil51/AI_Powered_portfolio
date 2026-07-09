from __future__ import annotations

from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.policies import KnowledgePolicies, default_knowledge_policies
from domain.knowledge.value_objects import DocumentType, EmbeddingStatus


class KnowledgeValidationError(Exception):
    pass


class KnowledgeValidator:
    def __init__(self, policies: KnowledgePolicies | None = None) -> None:
        self._policies = policies or default_knowledge_policies

    def validate_create(self, title: str, doc_type: DocumentType | None = None) -> None:
        if not title or not title.strip():
            raise KnowledgeValidationError("Document title is required")
        if doc_type is not None and not self._policies.is_allowed_type(doc_type):
            raise KnowledgeValidationError(f"Document type '{doc_type.value}' is not allowed")

    def validate_upload(self, document: KnowledgeDocument) -> None:
        if document.is_terminal:
            raise KnowledgeValidationError(
                f"Cannot upload document in terminal state: {document.status.value}"
            )
        if document.source.size_bytes > self._policies.max_document_size_bytes:
            raise KnowledgeValidationError(
                f"Document size {document.source.size_bytes} exceeds maximum {self._policies.max_document_size_bytes}"
            )

    def validate_chunk(self, chunk: KnowledgeChunk) -> None:
        if not chunk.text.strip():
            raise KnowledgeValidationError("Chunk text cannot be empty")
        if self._policies.min_chunk_size > 0 and chunk.character_count < self._policies.min_chunk_size:
            raise KnowledgeValidationError(
                f"Chunk character count {chunk.character_count} is below minimum {self._policies.min_chunk_size}"
            )

    def validate_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        if not chunks:
            raise KnowledgeValidationError("At least one chunk is required")
        if len(chunks) > self._policies.max_chunks_per_document:
            raise KnowledgeValidationError(
                f"Chunk count {len(chunks)} exceeds maximum {self._policies.max_chunks_per_document}"
            )
        for chunk in chunks:
            self.validate_chunk(chunk)

    def validate_embedding(self, chunk: KnowledgeChunk) -> None:
        if chunk.is_empty:
            raise KnowledgeValidationError("Cannot embed an empty chunk")
        if chunk.embedding_status == EmbeddingStatus.FAILED:
            raise KnowledgeValidationError("Cannot embed a chunk that previously failed")

    def validate_version_transition(self, document: KnowledgeDocument) -> None:
        if document.is_terminal:
            raise KnowledgeValidationError(
                f"Cannot change version of document in terminal state: {document.status.value}"
            )
