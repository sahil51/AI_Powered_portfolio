from __future__ import annotations

from typing import Any

from application.knowledge_context.models import ContextMetricsData


class KnowledgeContextMetricsCollector:
    def __init__(self) -> None:
        self._metrics = ContextMetricsData()

    def record_retrieval(
        self,
        chunks_retrieved: int,
        latency_ms: float,
        cache_hit: bool = False,
    ) -> None:
        self._metrics.total_retrievals += 1
        if cache_hit:
            self._metrics.cache_hits += 1
        else:
            self._metrics.cache_misses += 1
        self._metrics.total_chunks_retrieved += chunks_retrieved
        self._metrics.total_latency_ms += latency_ms

    def record_tokens(self, tokens_used: int) -> None:
        self._metrics.total_tokens_used += tokens_used

    def record_compression(self, tokens_saved: int) -> None:
        self._metrics.compressions_performed += 1
        self._metrics.tokens_saved_by_compression += tokens_saved

    def reset(self) -> None:
        self._metrics = ContextMetricsData()

    def get_metrics(self) -> dict[str, Any]:
        m = self._metrics
        return {
            "total_retrievals": m.total_retrievals,
            "cache_hits": m.cache_hits,
            "cache_misses": m.cache_misses,
            "cache_hit_ratio": m.cache_hits / max(m.total_retrievals, 1),
            "total_chunks_retrieved": m.total_chunks_retrieved,
            "total_tokens_used": m.total_tokens_used,
            "average_latency_ms": m.total_latency_ms / max(m.total_retrievals, 1),
            "compressions_performed": m.compressions_performed,
            "tokens_saved_by_compression": m.tokens_saved_by_compression,
        }

    @property
    def metrics(self) -> ContextMetricsData:
        return self._metrics
