from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from application.retrieval.models import ScoreStrategy, SearchMode


@dataclass
class RetrievalMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    requests_by_mode: dict[str, int] = field(default_factory=dict)
    requests_by_strategy: dict[str, int] = field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0
    avg_result_count: float = 0.0
    avg_rerank_count: float = 0.0
    last_request_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class RetrievalMetricsCollector:
    def __init__(self) -> None:
        self._metrics = RetrievalMetrics()
        self._start_time = time.time()

    @property
    def metrics(self) -> RetrievalMetrics:
        return self._metrics

    def record_request(
        self,
        mode: SearchMode,
        latency_ms: float,
        success: bool = True,
        cache_hit: bool = False,
        strategy: ScoreStrategy | None = None,
    ) -> None:
        self._metrics.total_requests += 1

        mode_key = mode.value
        self._metrics.requests_by_mode[mode_key] = self._metrics.requests_by_mode.get(mode_key, 0) + 1

        if strategy:
            strat_key = strategy.value
            self._metrics.requests_by_strategy[strat_key] = self._metrics.requests_by_strategy.get(strat_key, 0) + 1

        if success:
            self._metrics.successful_requests += 1
        else:
            self._metrics.failed_requests += 1

        if cache_hit:
            self._metrics.cache_hits += 1
        else:
            self._metrics.cache_misses += 1

        self._metrics.total_latency_ms += latency_ms
        self._metrics.avg_latency_ms = self._metrics.total_latency_ms / self._metrics.total_requests
        self._metrics.max_latency_ms = max(self._metrics.max_latency_ms, latency_ms)
        self._metrics.min_latency_ms = (
            latency_ms if self._metrics.min_latency_ms == 0.0 else min(self._metrics.min_latency_ms, latency_ms)
        )
        self._metrics.last_request_at = datetime.now(timezone.utc)

    def record_result_count(self, count: int) -> None:
        total = self._metrics.total_requests or 1
        self._metrics.avg_result_count = (
            (self._metrics.avg_result_count * (total - 1) + count) / total
        )

    def record_rerank_count(self, count: int) -> None:
        total = self._metrics.total_requests or 1
        self._metrics.avg_rerank_count = (
            (self._metrics.avg_rerank_count * (total - 1) + count) / total
        )

    def reset(self) -> None:
        self._metrics = RetrievalMetrics()
        self._start_time = time.time()
