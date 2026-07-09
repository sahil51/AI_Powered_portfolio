from __future__ import annotations

from application.knowledge_context.models import ContextStatisticsData


class KnowledgeContextStatisticsCollector:
    def __init__(self) -> None:
        self._stats = ContextStatisticsData()

    def record_request(
        self,
        success: bool,
        chunks_served: int = 0,
        tokens_served: int = 0,
        latency_ms: float = 0.0,
        truncated: bool = False,
    ) -> None:
        self._stats.total_requests += 1
        if success:
            self._stats.successful_requests += 1
        else:
            self._stats.failed_requests += 1
        if truncated:
            self._stats.truncated_responses += 1
        self._stats.total_chunks_served += chunks_served
        self._stats.total_tokens_served += tokens_served

        total = self._stats.total_requests
        self._stats.average_latency_ms = (
            (self._stats.average_latency_ms * (total - 1) + latency_ms) / total
        )

    def record_knowledge_coverage(self, doc_type: str) -> None:
        self._stats.knowledge_coverage[doc_type] = (
            self._stats.knowledge_coverage.get(doc_type, 0) + 1
        )

    def record_error(self, error_type: str) -> None:
        self._stats.errors_by_type[error_type] = (
            self._stats.errors_by_type.get(error_type, 0) + 1
        )

    def get_statistics(self) -> ContextStatisticsData:
        return self._stats

    def reset(self) -> None:
        self._stats = ContextStatisticsData()
