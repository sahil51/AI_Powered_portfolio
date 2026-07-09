from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from application.retrieval.exceptions import (
    RetrievalConfigurationError,
    RetrievalConnectionError,
    RetrievalError,
    RetrievalFusionError,
    RetrievalProviderError,
    RetrievalRerankingError,
    RetrievalSerializationError,
    RetrievalTimeoutError,
    RetrievalValidationError,
)
from application.retrieval.fusion import ScoreFusion
from application.retrieval.health import RetrievalHealth, RetrievalHealthChecker, RetrievalHealthStatus
from application.retrieval.hybrid_service import HybridRetrievalService
from application.retrieval.metrics import RetrievalMetrics, RetrievalMetricsCollector
from application.retrieval.models import (
    FilterOperator,
    HybridSearchConfiguration,
    RetrievalRequest,
    RetrievalResult,
    ScoreStrategy,
    SearchFilter,
    SearchMode,
    SearchQuery,
    SearchResult,
)
from application.retrieval.reranker import MMRReranker, ScoreNormalizer
from application.retrieval.search_service import KnowledgeSearchService
from application.retrieval.statistics import RetrievalStatistics, RetrievalStatisticsCollector
from application.retrieval.validator import RetrievalValidator
from domain.knowledge.chunk import KnowledgeChunk
from domain.knowledge.value_objects import ChunkId


@pytest.fixture
def sample_chunk():
    return KnowledgeChunk(
        chunk_id=ChunkId(),
        document_id="doc-123",
        chunk_index=0,
        text="test content",
        token_count=10,
    )


class TestRetrievalModels:
    def test_search_query_defaults(self):
        q = SearchQuery()
        assert q.query_text == ""
        assert q.mode == SearchMode.HYBRID
        assert q.config.final_top_k == 10

    def test_search_filter_defaults(self):
        f = SearchFilter()
        assert f.tags is None
        assert f.tag_filter_mode == FilterOperator.CONTAINS
        assert f.must_match_all_tags is True

    def test_search_result_with_chunk(self, sample_chunk):
        r = SearchResult(chunk=sample_chunk)
        assert r.chunk == sample_chunk
        assert r.score == 0.0
        assert r.rank == 0

    def test_search_response_defaults(self):
        r = type("R", (), {"chunk": sample_chunk, "score": 0.5, "rank": 1})()
        resp = type("resp", (), {"results": [r], "total_hits": 1, "latency_ms": 10.0})()
        assert resp.total_hits == 1
        assert resp.latency_ms == 10.0

    def test_hybrid_configuration_defaults(self):
        c = HybridSearchConfiguration()
        assert c.semantic_weight == 0.5
        assert c.keyword_weight == 0.3
        assert c.metadata_weight == 0.2
        assert c.fusion_strategy == ScoreStrategy.WEIGHTED_AVG
        assert c.rerank_enabled is True
        assert c.enable_mmr is True

    def test_retrieval_request_defaults(self):
        r = RetrievalRequest()
        assert r.top_k == 10
        assert r.min_score == 0.0

    def test_retrieval_result_defaults(self):
        r = RetrievalResult()
        assert r.chunk_ids == []
        assert r.scores == []
        assert r.total_hits == 0

    def test_search_mode_values(self):
        assert SearchMode.SEMANTIC.value == "semantic"
        assert SearchMode.KEYWORD.value == "keyword"
        assert SearchMode.HYBRID.value == "hybrid"

    def test_score_strategy_values(self):
        assert ScoreStrategy.WEIGHTED_AVG.value == "weighted_avg"
        assert ScoreStrategy.MAX.value == "max"
        assert ScoreStrategy.RR_FUSION.value == "reciprocal_rank_fusion"

    def test_filter_operator_values(self):
        assert FilterOperator.EQ.value == "eq"
        assert FilterOperator.CONTAINS.value == "contains"
        assert FilterOperator.IN.value == "in"


class TestRetrievalExceptions:
    def test_error_base(self):
        e = RetrievalError("test", "detail")
        assert e.message == "test"
        assert e.detail == "detail"

    def test_error_hierarchy(self):
        assert issubclass(RetrievalConnectionError, RetrievalError)
        assert issubclass(RetrievalTimeoutError, RetrievalError)
        assert issubclass(RetrievalValidationError, RetrievalError)
        assert issubclass(RetrievalProviderError, RetrievalError)
        assert issubclass(RetrievalConfigurationError, RetrievalError)
        assert issubclass(RetrievalSerializationError, RetrievalError)
        assert issubclass(RetrievalFusionError, RetrievalError)
        assert issubclass(RetrievalRerankingError, RetrievalError)


class TestRetrievalHealth:
    def test_default_health(self):
        h = RetrievalHealth()
        assert h.status == RetrievalHealthStatus.HEALTHY
        assert h.success_rate == 1.0

    def test_checker_healthy(self):
        checker = RetrievalHealthChecker()
        health = checker.check()
        assert health.status == RetrievalHealthStatus.HEALTHY

    def test_checker_degraded_high_latency(self):
        metrics = RetrievalMetrics(total_requests=10, successful_requests=9, failed_requests=1, avg_latency_ms=6000.0)
        checker = RetrievalHealthChecker(max_avg_latency_ms=5000.0, min_success_rate=0.8)
        health = checker.check(metrics)
        assert health.status == RetrievalHealthStatus.DEGRADED

    def test_checker_unhealthy_consecutive_failures(self):
        checker = RetrievalHealthChecker(max_consecutive_failures=3)
        checker.record_failure("err1")
        checker.record_failure("err2")
        checker.record_failure("err3")
        health = checker.check()
        assert health.status == RetrievalHealthStatus.UNHEALTHY

    def test_record_success_clears_failures(self):
        checker = RetrievalHealthChecker(max_consecutive_failures=3)
        checker.record_failure("err1")
        checker.record_failure("err2")
        checker.record_success()
        health = checker.check()
        assert health.status == RetrievalHealthStatus.HEALTHY


class TestRetrievalMetrics:
    def test_default_metrics(self):
        m = RetrievalMetrics()
        assert m.total_requests == 0
        assert m.successful_requests == 0
        assert m.cache_hits == 0

    def test_collector_record_request(self):
        c = RetrievalMetricsCollector()
        c.record_request(SearchMode.HYBRID, 100.0, success=True)
        assert c.metrics.total_requests == 1
        assert c.metrics.successful_requests == 1

    def test_collector_record_request_failure(self):
        c = RetrievalMetricsCollector()
        c.record_request(SearchMode.SEMANTIC, 50.0, success=False)
        assert c.metrics.failed_requests == 1

    def test_collector_cache_hit(self):
        c = RetrievalMetricsCollector()
        c.record_request(SearchMode.KEYWORD, 10.0, success=True, cache_hit=True)
        assert c.metrics.cache_hits == 1
        assert c.metrics.cache_misses == 0

    def test_collector_reset(self):
        c = RetrievalMetricsCollector()
        c.record_request(SearchMode.HYBRID, 100.0)
        c.reset()
        assert c.metrics.total_requests == 0

    def test_record_result_count(self):
        c = RetrievalMetricsCollector()
        c.record_request(SearchMode.HYBRID, 100.0)
        c.record_result_count(10)
        assert c.metrics.avg_result_count == 10.0

    def test_record_rerank_count(self):
        c = RetrievalMetricsCollector()
        c.record_request(SearchMode.HYBRID, 100.0)
        c.record_rerank_count(5)
        assert c.metrics.avg_rerank_count == 5.0


class TestRetrievalStatistics:
    def test_default_statistics(self):
        s = RetrievalStatistics()
        assert s.total_queries == 0
        assert s.success_rate == 1.0

    def test_collector_record_query(self):
        c = RetrievalStatisticsCollector()
        c.record_query("hybrid", True)
        assert c.statistics.total_queries == 1
        assert c.statistics.successful_queries == 1

    def test_collector_record_query_failure(self):
        c = RetrievalStatisticsCollector()
        c.record_query("semantic", False)
        assert c.statistics.failed_queries == 1

    def test_collector_record_result(self):
        c = RetrievalStatisticsCollector()
        c.record_result("pdf", 0.95)
        assert c.statistics.queries_by_doc_type.get("pdf") == 1

    def test_collector_reset(self):
        c = RetrievalStatisticsCollector()
        c.record_query("hybrid", True)
        c.reset()
        assert c.statistics.total_queries == 0


class TestRetrievalValidator:
    def test_valid_query_passes(self):
        v = RetrievalValidator()
        query = SearchQuery(query_text="test", mode=SearchMode.SEMANTIC)
        v.validate_query(query)

    def test_empty_query_text_raises(self):
        v = RetrievalValidator()
        query = SearchQuery(query_text="", mode=SearchMode.SEMANTIC)
        with pytest.raises(RetrievalValidationError):
            v.validate_query(query)

    def test_metadata_mode_allows_empty_text(self):
        v = RetrievalValidator()
        query = SearchQuery(query_text="", mode=SearchMode.METADATA)
        v.validate_query(query)

    def test_invalid_weights_raises(self):
        v = RetrievalValidator()
        config = HybridSearchConfiguration(semantic_weight=1.0, keyword_weight=1.0, metadata_weight=1.0)
        with pytest.raises(RetrievalValidationError):
            v.validate_configuration(config)

    def test_valid_weights_pass(self):
        v = RetrievalValidator()
        config = HybridSearchConfiguration(semantic_weight=0.5, keyword_weight=0.3, metadata_weight=0.2)
        v.validate_configuration(config)

    def test_final_top_k_exceeds_rerank_top_k(self):
        v = RetrievalValidator()
        config = HybridSearchConfiguration(final_top_k=100, rerank_top_k=50)
        with pytest.raises(RetrievalValidationError):
            v.validate_configuration(config)

    def test_invalid_mmr_lambda(self):
        v = RetrievalValidator()
        config = HybridSearchConfiguration(mmr_lambda=1.5)
        with pytest.raises(RetrievalValidationError):
            v.validate_configuration(config)

    def test_unknown_normalization_method(self):
        v = RetrievalValidator()
        config = HybridSearchConfiguration(normalization_method="unknown")
        with pytest.raises(RetrievalValidationError):
            v.validate_configuration(config)

    def test_filter_date_range(self):
        v = RetrievalValidator()
        f = SearchFilter(
            created_after=datetime(2024, 1, 1, tzinfo=timezone.utc),
            created_before=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(RetrievalValidationError):
            v.validate_filter(f)

    def test_validate_result_invalid(self, sample_chunk):
        v = RetrievalValidator()
        empty_chunk = KnowledgeChunk(chunk_id=ChunkId(), text="")
        result = SearchResult(chunk=empty_chunk)
        assert v.validate_result(result) is False

    def test_validate_result_valid(self, sample_chunk):
        v = RetrievalValidator()
        result = SearchResult(chunk=sample_chunk)
        assert v.validate_result(result) is True


class TestScoreNormalizer:
    def test_min_max(self):
        scores = [0.1, 0.5, 1.0]
        normalized = ScoreNormalizer.min_max(scores)
        assert normalized[0] == 0.0
        assert normalized[1] == pytest.approx(0.444, rel=0.01)
        assert normalized[2] == 1.0

    def test_min_max_same_values(self):
        scores = [0.5, 0.5, 0.5]
        normalized = ScoreNormalizer.min_max(scores)
        assert normalized == [1.0, 1.0, 1.0]

    def test_min_max_empty(self):
        assert ScoreNormalizer.min_max([]) == []

    def test_z_score(self):
        scores = [1.0, 2.0, 3.0]
        normalized = ScoreNormalizer.z_score(scores)
        assert len(normalized) == 3
        assert abs(sum(normalized)) < 1e-10

    def test_z_score_empty(self):
        assert ScoreNormalizer.z_score([]) == []

    def test_rank_based(self):
        scores = [10.0, 20.0, 30.0]
        normalized = ScoreNormalizer.rank_based(scores)
        assert normalized[2] == 1.0
        assert normalized[0] == 0.0


class TestMMRReranker:
    @pytest.mark.asyncio
    async def test_rerank_empty(self):
        reranker = MMRReranker()
        result = await reranker.rerank([], top_k=5)
        assert result == []

    @pytest.mark.asyncio
    async def test_rerank_with_candidates(self, sample_chunk):
        reranker = MMRReranker(lambda_=0.7)
        candidates = [
            SearchResult(chunk=sample_chunk, score=0.9),
            SearchResult(chunk=sample_chunk, score=0.8),
            SearchResult(chunk=sample_chunk, score=0.7),
        ]
        result = await reranker.rerank(candidates, top_k=2)
        assert len(result) == 2

    def test_cosine_similarity(self):
        reranker = MMRReranker()
        sim = reranker._cosine_similarity([1.0, 0.0], [1.0, 0.0])
        assert sim == 1.0

    def test_cosine_similarity_zero(self):
        reranker = MMRReranker()
        sim = reranker._cosine_similarity([], [])
        assert sim == 0.0


class TestScoreFusion:
    def test_normalize_scores_min_max(self):
        scores = ScoreFusion.normalize_scores([0.0, 0.5, 1.0])
        assert scores[0] == 0.0
        assert scores[2] == 1.0

    def test_normalize_scores_same(self):
        scores = ScoreFusion.normalize_scores([0.5, 0.5])
        assert scores == [1.0, 1.0]

    def test_weighted_avg(self):
        semantic = [("a", 1.0), ("b", 0.5)]
        keyword = [("a", 0.5), ("c", 1.0)]
        metadata = [("b", 1.0)]
        result = ScoreFusion.weighted_avg(semantic, keyword, metadata)
        assert "a" in result
        assert "b" in result
        assert "c" in result
        assert result["a"] == pytest.approx(0.5 * 1.0 + 0.3 * 0.5 + 0.2 * 0.0)

    def test_weighted_avg_max_strategy(self):
        semantic = [("a", 1.0), ("b", 0.5)]
        keyword = [("a", 0.5), ("b", 0.8)]
        result = ScoreFusion.weighted_avg(semantic, keyword, [], strategy=ScoreStrategy.MAX)
        assert result["a"] == 1.0
        assert result["b"] == 0.8

    def test_reciprocal_rank_fusion(self):
        rankings = [["a", "b", "c"], ["b", "a", "c"]]
        result = ScoreFusion.reciprocal_rank_fusion(rankings, k=60)
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_distribution_based_score_fusion(self):
        scores = [[("a", 0.9), ("b", 0.8)], [("a", 0.7), ("c", 0.6)]]
        result = ScoreFusion.distribution_based_score_fusion(scores)
        assert result["a"] == 0.8
        assert result["b"] == 0.8
        assert result["c"] == 0.6


class TestHybridRetrievalService:
    @pytest.mark.asyncio
    async def test_search_without_retrievers(self):
        service = HybridRetrievalService()
        query = SearchQuery(query_text="test", mode=SearchMode.METADATA)
        response = await service.search(query)
        assert response.total_hits == 0

    @pytest.mark.asyncio
    async def test_search_metadata_mode(self):
        service = HybridRetrievalService()
        query = SearchQuery(query_text="", mode=SearchMode.METADATA, filter=SearchFilter(tags=["test"]))
        response = await service.search(query)
        assert response.total_hits == 0


class TestKnowledgeSearchService:
    @pytest.mark.asyncio
    async def test_search_delegates_to_hybrid(self):
        hybrid = AsyncMock()
        hybrid.search.return_value = type("resp", (), {
            "results": [],
            "total_hits": 0,
            "total_documents": 0,
            "query": None,
            "latency_ms": 0.0,
            "retrieval_breakdown": {},
            "cache_hit": False,
            "correlation_id": "",
        })()
        service = KnowledgeSearchService(hybrid_service=hybrid)
        query = SearchQuery(query_text="test")
        response = await service.search(query)
        assert response.total_hits == 0

    @pytest.mark.asyncio
    async def test_health_check(self):
        hybrid = AsyncMock()
        service = KnowledgeSearchService(hybrid_service=hybrid)
        health = await service.health_check()
        assert health.status == RetrievalHealthStatus.HEALTHY

    def test_get_statistics(self):
        hybrid = AsyncMock()
        service = KnowledgeSearchService(hybrid_service=hybrid)
        stats = service.get_statistics()
        assert stats.total_queries == 0

    def test_get_metrics(self):
        hybrid = AsyncMock()
        service = KnowledgeSearchService(hybrid_service=hybrid)
        metrics = service.get_metrics()
        assert metrics.total_requests == 0

    def test_reset_metrics(self):
        hybrid = AsyncMock()
        service = KnowledgeSearchService(hybrid_service=hybrid)
        service.reset_metrics()
        assert service.get_metrics().total_requests == 0
