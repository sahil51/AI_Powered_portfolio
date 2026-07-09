from __future__ import annotations

import time

from application.embedding.interfaces import EmbeddingProvider
from application.retrieval.exceptions import RetrievalError
from application.retrieval.health import RetrievalHealth, RetrievalHealthChecker
from application.retrieval.hybrid_service import HybridRetrievalService
from application.retrieval.metrics import RetrievalMetrics, RetrievalMetricsCollector
from application.retrieval.models import SearchFilter, SearchMode, SearchQuery, SearchResponse
from application.retrieval.statistics import RetrievalStatistics, RetrievalStatisticsCollector
from application.retrieval.validator import RetrievalValidator


class KnowledgeSearchService:
    def __init__(
        self,
        hybrid_service: HybridRetrievalService,
        embedding_provider: EmbeddingProvider | None = None,
        validator: RetrievalValidator | None = None,
        metrics_collector: RetrievalMetricsCollector | None = None,
        statistics_collector: RetrievalStatisticsCollector | None = None,
        health_checker: RetrievalHealthChecker | None = None,
    ) -> None:
        self._hybrid_service = hybrid_service
        self._embedding_provider = embedding_provider
        self._validator = validator or RetrievalValidator()
        self._metrics = metrics_collector or RetrievalMetricsCollector()
        self._statistics = statistics_collector or RetrievalStatisticsCollector()
        self._health = health_checker or RetrievalHealthChecker()

    async def search(self, query: SearchQuery) -> SearchResponse:
        start = time.time()
        try:
            self._validator.validate_query(query)
            response = await self._hybrid_service.search(query)
            latency_ms = (time.time() - start) * 1000
            self._metrics.record_request(
                mode=query.mode,
                latency_ms=latency_ms,
                success=True,
                strategy=query.config.fusion_strategy,
            )
            self._statistics.record_query(mode=query.mode.value, success=True)
            self._statistics.record_latency(latency_ms)
            self._health.record_success()
            return response
        except RetrievalError:
            raise
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            self._metrics.record_request(mode=query.mode, latency_ms=latency_ms, success=False)
            self._statistics.record_query(mode=query.mode.value, success=False)
            self._health.record_failure(str(e))
            raise RetrievalError(message="Search failed", detail=str(e))

    async def search_by_text(
        self,
        text: str,
        top_k: int = 10,
        filter: SearchFilter | None = None,
    ) -> SearchResponse:
        from application.retrieval.models import HybridSearchConfiguration
        from application.retrieval.models import SearchFilter as SearchFilterAlias

        query = SearchQuery(
            query_text=text,
            mode=SearchMode.HYBRID,
            filter=filter or SearchFilterAlias(),
            config=HybridSearchConfiguration(final_top_k=top_k),
        )
        return await self.search(query)

    async def search_semantic(self, query: SearchQuery) -> SearchResponse:
        query.mode = SearchMode.SEMANTIC
        return await self.search(query)

    async def search_keyword(self, query: SearchQuery) -> SearchResponse:
        query.mode = SearchMode.KEYWORD
        return await self.search(query)

    async def health_check(self) -> RetrievalHealth:
        return self._health.check(self._metrics.metrics)

    def get_statistics(self) -> RetrievalStatistics:
        return self._statistics.statistics

    def get_metrics(self) -> RetrievalMetrics:
        return self._metrics.metrics

    def reset_metrics(self) -> None:
        self._metrics.reset()
