from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from domain.knowledge.value_objects import ChunkingStrategy


class EmbeddingProviderType(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    NVIDIA = "nvidia"
    VOYAGE = "voyage"
    COHERE = "cohere"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    CUSTOM = "custom"


@dataclass
class EmbeddingRequest:
    chunk_id: str = ""
    text: str = ""
    model: str = ""
    provider: EmbeddingProviderType = EmbeddingProviderType.CUSTOM
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    chunk_id: str = ""
    embedding: list[float] = field(default_factory=list)
    dimension: int = 0
    model: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingMetadata:
    model: str = ""
    provider: EmbeddingProviderType = EmbeddingProviderType.CUSTOM
    dimension: int = 0
    tokens_used: int = 0
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingConfiguration:
    provider: EmbeddingProviderType = EmbeddingProviderType.CUSTOM
    model: str = ""
    api_key: str = ""
    dimensions: int = 768
    max_retries: int = 3
    timeout: float = 30.0
    batch_size: int = 32
    max_tokens_per_chunk: int = 8191
    overlap_tokens: int = 200
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    enable_deduplication: bool = True


@dataclass
class EmbeddingBatchResult:
    document_id: str = ""
    chunks: list[str] = field(default_factory=list)
    embeddings: list[list[float]] = field(default_factory=list)
    success: bool = False
    error: str | None = None
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
