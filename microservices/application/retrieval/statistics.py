from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RetrievalStatistics:
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    queries_by_mode: dict[str, int] = field(default_factory=dict)
    queries_by_strategy: dict[str, int] = field(default_factory=dict)
    queries_by_doc_type: dict[str, int] = field(default_factory=dict)
    avg_latency_ms: float = 0.0
    avg_results_per_query: float = 0.0
    success_rate: float = 1.0
    unique_query_terms: int = 0


class RetrievalStatisticsCollector:
    def __init__(self) -> None:
        self._stats = RetrievalStatistics()
        self._total_latency: float = 0.0
        self._total_results: int = 0

    @property
    def statistics(self) -> RetrievalStatistics:
        return self._stats

    def record_query(self, mode: str, success: bool) -> None:
        self._stats.total_queries += 1
        if success:
            self._stats.successful_queries += 1
        else:
            self._stats.failed_queries += 1
        self._stats.queries_by_mode[mode] = self._stats.queries_by_mode.get(mode, 0) + 1
        self._update_rates()

    def record_result(self, doc_type: str, score: float) -> None:
        self._stats.queries_by_doc_type[doc_type] = self._stats.queries_by_doc_type.get(doc_type, 0) + 1

    def record_latency(self, latency_ms: float) -> None:
        self._total_latency += latency_ms
        if self._stats.total_queries > 0:
            self._stats.avg_latency_ms = self._total_latency / self._stats.total_queries

    def _update_rates(self) -> None:
        if self._stats.total_queries > 0:
            self._stats.success_rate = self._stats.successful_queries / self._stats.total_queries

    def reset(self) -> None:
        self._stats = RetrievalStatistics()
        self._total_latency = 0.0
        self._total_results = 0
