from __future__ import annotations

from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.factory import KnowledgeFactory
from domain.knowledge.metadata import KnowledgeMetadata
from domain.knowledge.policies import KnowledgePolicies
from domain.knowledge.validator import KnowledgeValidator
from domain.knowledge.value_objects import (
    ChunkingStrategy,
    DocumentSource,
    DocumentType,
)


class KnowledgeLifecycle:
    def __init__(
        self,
        validator: KnowledgeValidator | None = None,
        factory: KnowledgeFactory | None = None,
    ) -> None:
        self._validator = validator or KnowledgeValidator()
        self._factory = factory or KnowledgeFactory(self._validator)

    def create_document(
        self,
        title: str,
        doc_type: DocumentType = DocumentType.CUSTOM,
        source: DocumentSource | None = None,
        policies: KnowledgePolicies | None = None,
        correlation_id: str = "",
        metadata: KnowledgeMetadata | None = None,
        tags: list[str] | None = None,
    ) -> KnowledgeDocument:
        return self._factory.create(
            title=title,
            doc_type=doc_type,
            source=source,
            policies=policies,
            correlation_id=correlation_id,
            metadata=metadata,
            tags=tags,
        )

    def upload(self, document: KnowledgeDocument) -> None:
        self._validator.validate_upload(document)
        document.upload()

    def start_processing(self, document: KnowledgeDocument) -> None:
        document.start_processing()

    def chunk(
        self,
        document: KnowledgeDocument,
        chunks: list[KnowledgeChunk],
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE,
    ) -> None:
        self._validator.validate_chunks(chunks)
        document.chunks = chunks
        document.chunk(chunk_count=len(chunks), chunking_strategy=chunking_strategy)

    def embed(self, document: KnowledgeDocument) -> None:
        for chunk in document.chunks:
            self._validator.validate_embedding(chunk)
        document.embed()

    def index(self, document: KnowledgeDocument) -> None:
        document.index()

    def activate(self, document: KnowledgeDocument) -> None:
        if document.policies.auto_activate:
            document.activate()
