from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from domain.knowledge.aggregate import KnowledgeDocument
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.metadata import KnowledgeMetadata
from domain.knowledge.policies import KnowledgePolicies, default_knowledge_policies
from domain.knowledge.state import KnowledgeStateMachine
from domain.knowledge.validator import KnowledgeValidator
from domain.knowledge.value_objects import (
    ChunkId,
    DocumentId,
    DocumentSource,
    DocumentType,
    KnowledgeStatus,
    KnowledgeVersion,
)


class KnowledgeFactory:
    def __init__(self, validator: KnowledgeValidator | None = None) -> None:
        self._validator = validator or KnowledgeValidator()

    def create(
        self,
        title: str,
        doc_type: DocumentType = DocumentType.CUSTOM,
        source: DocumentSource | None = None,
        policies: KnowledgePolicies | None = None,
        correlation_id: str = "",
        metadata: KnowledgeMetadata | None = None,
        tags: list[str] | None = None,
    ) -> KnowledgeDocument:
        self._validator.validate_create(title, doc_type)

        return KnowledgeDocument(
            document_id=DocumentId(),
            title=title,
            doc_type=doc_type,
            source=source or DocumentSource(),
            state_machine=KnowledgeStateMachine(),
            policies=policies or default_knowledge_policies,
            metadata=metadata or KnowledgeMetadata(),
            correlation_id=correlation_id,
            tags=tags or [],
            version=KnowledgeVersion(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def restore(
        self,
        document_id: str,
        title: str,
        doc_type: str = "custom",
        source: dict[str, Any] | None = None,
        chunks: list[dict[str, Any]] | None = None,
        status: str = "created",
        policies: KnowledgePolicies | None = None,
        correlation_id: str = "",
        metadata: KnowledgeMetadata | None = None,
        tags: list[str] | None = None,
        version: str = "1.0.0",
        checksum: str = "",
        error: str = "",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        processed_at: datetime | None = None,
        embedded_at: datetime | None = None,
        indexed_at: datetime | None = None,
    ) -> KnowledgeDocument:
        did = DocumentId()
        object.__setattr__(did, "value", document_id)

        restored_source = DocumentSource()
        if source:
            restored_source.filename = source.get("filename", "")
            restored_source.path = source.get("path", "")
            restored_source.url = source.get("url", "")
            restored_source.mime_type = source.get("mime_type", "")
            restored_source.size_bytes = source.get("size_bytes", 0)
            restored_source.encoding = source.get("encoding", "utf-8")
            restored_source.metadata = source.get("metadata", {})

        restored_chunks: list[KnowledgeChunk] = []
        if chunks:
            for c in chunks:
                cid = ChunkId()
                object.__setattr__(cid, "value", c.get("chunk_id", ""))
                restored_chunks.append(
                    KnowledgeChunk(
                        chunk_id=cid,
                        document_id=c.get("document_id", ""),
                        chunk_index=c.get("chunk_index", 0),
                        text=c.get("text", ""),
                        token_count=c.get("token_count", 0),
                        character_count=c.get("character_count", 0),
                        section=c.get("section", ""),
                        heading=c.get("heading", ""),
                        metadata=c.get("metadata", {}),
                        language=c.get("language", "en"),
                        checksum=c.get("checksum", ""),
                        embedding=c.get("embedding"),
                        embedding_dimension=c.get("embedding_dimension", 0),
                        embedding_model=c.get("embedding_model", ""),
                    )
                )

        doc_version = KnowledgeVersion(version)

        return KnowledgeDocument(
            document_id=did,
            title=title,
            doc_type=DocumentType(doc_type),
            source=restored_source,
            chunks=restored_chunks,
            state_machine=KnowledgeStateMachine(KnowledgeStatus(status)),
            policies=policies or default_knowledge_policies,
            metadata=metadata or KnowledgeMetadata(),
            correlation_id=correlation_id,
            tags=tags or [],
            version=doc_version,
            checksum=checksum,
            error=error,
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
            processed_at=processed_at,
            embedded_at=embedded_at,
            indexed_at=indexed_at,
        )
