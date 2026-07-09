from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.value_objects import DocumentType, KnowledgeStatus


class SearchMode(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    METADATA = "metadata"


class FilterOperator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    BETWEEN = "between"
    CONTAINS = "contains"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class ScoreStrategy(str, Enum):
    WEIGHTED_AVG = "weighted_avg"
    MAX = "max"
    MIN = "min"
    RR_FUSION = "reciprocal_rank_fusion"
    DBSF = "distribution_based_score_fusion"


@dataclass
class SearchFilter:
    tags: list[str] | None = None
    tag_filter_mode: FilterOperator = FilterOperator.CONTAINS
    status: KnowledgeStatus | None = None
    doc_type: DocumentType | None = None
    doc_types: list[DocumentType] | None = None
    author: str | None = None
    source_url: str | None = None
    language: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    updated_after: datetime | None = None
    updated_before: datetime | None = None
    min_chunk_index: int | None = None
    max_chunk_index: int | None = None
    section: str | None = None
    heading: str | None = None
    custom: dict[str, Any] = field(default_factory=dict)
    must_match_all_tags: bool = True


@dataclass
class HybridSearchConfiguration:
    semantic_weight: float = 0.5
    keyword_weight: float = 0.3
    metadata_weight: float = 0.2
    fusion_strategy: ScoreStrategy = ScoreStrategy.WEIGHTED_AVG
    rerank_enabled: bool = True
    rerank_top_k: int = 50
    final_top_k: int = 10
    enable_mmr: bool = True
    mmr_lambda: float = 0.7
    mmr_top_k: int = 20
    normalize_scores: bool = True
    normalization_method: str = "min_max"
    enable_query_expansion: bool = False
    query_expansion_strategy: str = "alternate_phrasing"
    min_semantic_score: float = 0.0
    min_keyword_score: float = 0.0
    min_hybrid_score: float = 0.0
    semantic_candidate_k: int = 100
    keyword_candidate_k: int = 100
    metadata_candidate_k: int = 100


@dataclass
class SearchQuery:
    query_text: str = ""
    query_embedding: list[float] | None = None
    mode: SearchMode = SearchMode.HYBRID
    filter: SearchFilter = field(default_factory=SearchFilter)
    config: HybridSearchConfiguration = field(default_factory=HybridSearchConfiguration)
    correlation_id: str = ""


@dataclass
class SearchResult:
    chunk: KnowledgeChunk
    document: Any | None = None
    score: float = 0.0
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    metadata_score: float = 0.0
    rerank_score: float = 0.0
    rank: int = 0
    matched_terms: list[str] = field(default_factory=list)
    explanation: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    results: list[SearchResult] = field(default_factory=list)
    total_hits: int = 0
    total_documents: int = 0
    query: SearchQuery | None = None
    latency_ms: float = 0.0
    retrieval_breakdown: dict[str, Any] = field(default_factory=dict)
    cache_hit: bool = False
    correlation_id: str = ""


@dataclass
class RetrievalRequest:
    embedding: list[float] | None = None
    query_text: str = ""
    top_k: int = 10
    filter: SearchFilter = field(default_factory=SearchFilter)
    min_score: float = 0.0
    vector_store_name: str = ""


@dataclass
class RetrievalResult:
    chunk_ids: list[str] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    chunks: list[KnowledgeChunk] = field(default_factory=list)
    latency_ms: float = 0.0
    total_hits: int = 0
    error: str | None = None
