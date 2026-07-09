from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from domain.knowledge.value_objects import DocumentId


class ImportStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    PARSING = "parsing"
    NORMALIZING = "normalizing"
    CHUNKING = "chunking"
    DEDUPLICATING = "deduplicating"
    EMBEDDING = "embedding"
    STORING = "storing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImportSourceType(Enum):
    FILE_UPLOAD = "file_upload"
    URL = "url"
    WEBSITE = "website"
    API = "api"
    WEBHOOK = "webhook"
    BULK = "bulk"


@dataclass
class ImportSource:
    source_type: ImportSourceType
    file_path: str = ""
    url: str = ""
    content: str = ""
    filename: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    title: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    sections: list[tuple[str, str, int]] = field(default_factory=list)
    language: str = "en"
    word_count: int = 0
    character_count: int = 0


@dataclass
class NormalizedDocument:
    title: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    sections: list[tuple[str, str, int]] = field(default_factory=list)
    language: str = "en"
    checksum: str = ""
    word_count: int = 0
    character_count: int = 0


@dataclass
class ImportBatchItem:
    source: ImportSource
    document_id: DocumentId | None = None
    status: ImportStatus = ImportStatus.PENDING
    error: str = ""
    parsed_document: ParsedDocument | None = None
    normalized_document: NormalizedDocument | None = None


@dataclass
class KnowledgeImportBatch:
    items: list[ImportBatchItem] = field(default_factory=list)
    batch_id: str = ""
    correlation_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    status: ImportStatus = ImportStatus.PENDING


@dataclass
class KnowledgeImportResult:
    document_id: DocumentId | None = None
    success: bool = False
    error: str = ""
    chunk_count: int = 0
    version: str = ""
    checksum: str = ""
    latency_ms: float = 0.0
    correlation_id: str = ""


@dataclass
class IngestionMetricsData:
    documents_imported: int = 0
    documents_failed: int = 0
    chunks_created: int = 0
    total_latency_ms: float = 0.0
    bytes_processed: int = 0
    tokens_used: int = 0
    duplicates_skipped: int = 0


@dataclass
class ImportStatisticsData:
    total_imports: int = 0
    successful_imports: int = 0
    failed_imports: int = 0
    total_chunks: int = 0
    total_bytes: int = 0
    total_latency_ms: float = 0.0
    imports_by_source: dict[str, int] = field(default_factory=dict)
    imports_by_type: dict[str, int] = field(default_factory=dict)
    errors_by_type: dict[str, int] = field(default_factory=dict)
