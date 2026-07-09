from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from domain.knowledge.chunk import KnowledgeChunk


class ContextSourcePriority(Enum):
    CONVERSATION = 0
    MEMORY = 1
    KNOWLEDGE = 2


class ChunkSelectionStrategy(Enum):
    RELEVANCE = "relevance"
    RECENCY = "recency"
    DIVERSITY = "diversity"
    HYBRID = "hybrid"


class CompressionStrategy(Enum):
    TRUNCATE = "truncate"
    SUMMARIZE = "summarize"
    EXTRACT = "extract"
    PRIORITIZE = "prioritize"


@dataclass
class KnowledgeContextChunk:
    chunk: KnowledgeChunk
    document_title: str = ""
    document_type: str = ""
    score: float = 0.0
    rank: int = 0
    source_priority: ContextSourcePriority = ContextSourcePriority.KNOWLEDGE


@dataclass
class KnowledgeContextConfig:
    max_knowledge_tokens: int = 2048
    max_retrieved_chunks: int = 20
    min_relevance_score: float = 0.3
    enable_compression: bool = True
    enable_deduplication: bool = True
    enable_section_grouping: bool = True
    enable_semantic_ordering: bool = False
    enable_metadata_preservation: bool = True
    enable_source_attribution: bool = True
    compression_strategy: CompressionStrategy = CompressionStrategy.TRUNCATE
    chunk_selection: ChunkSelectionStrategy = ChunkSelectionStrategy.RELEVANCE
    prefer_latest_version: bool = True
    excluded_doc_types: list[str] = field(default_factory=list)
    included_doc_types: list[str] = field(default_factory=list)
    language_filter: str = ""
    tenant_filter: str = ""


@dataclass
class TokenBudget:
    total_tokens: int = 8192
    conversation_tokens: int = 2048
    memory_tokens: int = 1024
    knowledge_tokens: int = 2048
    reserved_tokens: int = 1024
    used_tokens: int = 0
    remaining_tokens: int = 0

    def calculate_remaining(self) -> int:
        return self.total_tokens - self.used_tokens - self.reserved_tokens

    def can_accommodate(self, tokens: int) -> bool:
        return (self.used_tokens + tokens + self.reserved_tokens) <= self.total_tokens


@dataclass
class KnowledgeContextResult:
    chunks: list[KnowledgeContextChunk] = field(default_factory=list)
    total_chunks: int = 0
    total_tokens: int = 0
    truncated: bool = False
    compressed: bool = False
    deduplicated_count: int = 0
    retrieval_latency_ms: float = 0.0
    compression_latency_ms: float = 0.0
    cache_hit: bool = False
    query: str = ""
    correlation_id: str = ""


@dataclass
class AssembledContext:
    text: str = ""
    chunks: list[KnowledgeContextChunk] = field(default_factory=list)
    tokens_used: int = 0
    total_available: int = 0
    truncated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextMetricsData:
    total_retrievals: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_chunks_retrieved: int = 0
    total_tokens_used: int = 0
    total_latency_ms: float = 0.0
    compressions_performed: int = 0
    tokens_saved_by_compression: int = 0


@dataclass
class ContextStatisticsData:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    truncated_responses: int = 0
    total_chunks_served: int = 0
    total_tokens_served: int = 0
    average_latency_ms: float = 0.0
    knowledge_coverage: dict[str, int] = field(default_factory=dict)
    errors_by_type: dict[str, int] = field(default_factory=dict)
