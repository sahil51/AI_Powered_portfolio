from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from application.knowledge_ingestion.models import (
    ImportSource,
    NormalizedDocument,
    ParsedDocument,
)
from domain.knowledge.aggregate import KnowledgeDocument


class DocumentParser(ABC):
    @abstractmethod
    def supports(self, source: ImportSource) -> bool:
        ...

    @abstractmethod
    def parse(self, source: ImportSource) -> ParsedDocument:
        ...

    @abstractmethod
    def can_parse(self, mime_type: str, extension: str) -> bool:
        ...


class KnowledgeNormalizer(ABC):
    @abstractmethod
    def normalize(self, parsed: ParsedDocument) -> NormalizedDocument:
        ...


class KnowledgeDeduplicator(ABC):
    @abstractmethod
    def is_duplicate(self, checksum: str, document_id: str | None = None) -> bool:
        ...

    @abstractmethod
    def compute_checksum(self, content: str) -> str:
        ...

    @abstractmethod
    def mark_processed(self, checksum: str, document_id: str) -> None:
        ...

    @abstractmethod
    def find_duplicate_chunks(
        self, checksums: list[str], document_id: str | None = None
    ) -> set[int]:
        ...


class KnowledgeVersionManager(ABC):
    @abstractmethod
    def detect_changes(
        self, existing: KnowledgeDocument, incoming: NormalizedDocument
    ) -> list[str]:
        ...

    @abstractmethod
    def bump_version(self, current_version: str, changes: list[str]) -> str:
        ...

    @abstractmethod
    def should_reprocess(self, existing: KnowledgeDocument, changes: list[str]) -> bool:
        ...


class IngestionEventHandler(Protocol):
    def handle_knowledge_imported(self, document_id: str, **kwargs: Any) -> None:
        ...

    def handle_knowledge_updated(self, document_id: str, **kwargs: Any) -> None:
        ...

    def handle_knowledge_chunked(self, document_id: str, chunk_count: int, **kwargs: Any) -> None:
        ...

    def handle_knowledge_embedded(self, document_id: str, chunk_count: int, **kwargs: Any) -> None:
        ...

    def handle_knowledge_indexed(self, document_id: str, chunk_count: int, **kwargs: Any) -> None:
        ...

    def handle_knowledge_archived(self, document_id: str, reason: str, **kwargs: Any) -> None:
        ...

    def handle_knowledge_deleted(self, document_id: str, reason: str, **kwargs: Any) -> None:
        ...

    def handle_knowledge_import_failed(
        self, document_id: str, error: str, stage: str, **kwargs: Any
    ) -> None:
        ...
