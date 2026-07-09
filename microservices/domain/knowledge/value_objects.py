from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    TXT = "txt"
    HTML = "html"
    WEBSITE = "website"
    FAQ = "faq"
    POLICY = "policy"
    MANUAL = "manual"
    KNOWLEDGE_ARTICLE = "knowledge_article"
    CUSTOM = "custom"


class KnowledgeStatus(str, Enum):
    CREATED = "created"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    CHUNKED = "chunked"
    EMBEDDED = "embedded"
    INDEXED = "indexed"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ChunkingStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"
    SLIDING_WINDOW = "sliding_window"
    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"
    HEADING_AWARE = "heading_aware"
    SENTENCE = "sentence"


class EmbeddingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class DocumentId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DocumentId):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass(frozen=True)
class ChunkId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ChunkId):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass(frozen=True)
class KnowledgeVersion:
    value: str = "1.0.0"

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, KnowledgeVersion):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def bump_major(self) -> KnowledgeVersion:
        parts = self.value.split(".")
        return KnowledgeVersion(f"{int(parts[0]) + 1}.0.0")

    def bump_minor(self) -> KnowledgeVersion:
        parts = self.value.split(".")
        return KnowledgeVersion(f"{parts[0]}.{int(parts[1]) + 1}.0")

    def bump_patch(self) -> KnowledgeVersion:
        parts = self.value.split(".")
        return KnowledgeVersion(f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}")


def compute_checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class DocumentSource:
    filename: str = ""
    path: str = ""
    url: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    encoding: str = "utf-8"
    metadata: dict[str, Any] = field(default_factory=dict)
