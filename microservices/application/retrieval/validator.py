from __future__ import annotations

from application.retrieval.exceptions import RetrievalValidationError
from application.retrieval.models import HybridSearchConfiguration, SearchFilter, SearchMode, SearchQuery, SearchResult


class RetrievalValidator:
    def validate_query(self, query: SearchQuery) -> None:
        if not query.query_text.strip() and query.mode != SearchMode.METADATA:
            raise RetrievalValidationError("Query text must not be empty for semantic or keyword search")
        if query.mode == SearchMode.SEMANTIC and query.query_embedding is None and not query.query_text:
            raise RetrievalValidationError("Semantic search requires either query text or pre-computed embedding")
        if query.config.final_top_k <= 0:
            raise RetrievalValidationError("final_top_k must be greater than 0")
        if query.config.semantic_candidate_k <= 0:
            raise RetrievalValidationError("semantic_candidate_k must be greater than 0")
        self.validate_filter(query.filter)
        self.validate_configuration(query.config)

    def validate_filter(self, filter: SearchFilter) -> None:
        if filter.created_after and filter.created_before:
            if filter.created_after > filter.created_before:
                raise RetrievalValidationError("created_after must be before created_before")
        if filter.updated_after and filter.updated_before:
            if filter.updated_after > filter.updated_before:
                raise RetrievalValidationError("updated_after must be before updated_before")
        if filter.min_chunk_index is not None and filter.max_chunk_index is not None:
            if filter.min_chunk_index > filter.max_chunk_index:
                raise RetrievalValidationError("min_chunk_index must be <= max_chunk_index")

    def validate_configuration(self, config: HybridSearchConfiguration) -> None:
        total_weight = config.semantic_weight + config.keyword_weight + config.metadata_weight
        if abs(total_weight - 1.0) > 0.01:
            raise RetrievalValidationError(
                f"Hybrid weights must sum to 1.0, got {total_weight:.2f}"
            )
        if config.final_top_k > config.rerank_top_k:
            raise RetrievalValidationError("final_top_k must not exceed rerank_top_k")
        if not 0.0 <= config.mmr_lambda <= 1.0:
            raise RetrievalValidationError("mmr_lambda must be between 0 and 1")
        if config.normalization_method not in ("min_max", "z_score", "rank"):
            raise RetrievalValidationError(f"Unknown normalization method: {config.normalization_method}")

    def validate_result(self, result: SearchResult) -> bool:
        if not result.chunk or not result.chunk.text:
            return False
        return True
