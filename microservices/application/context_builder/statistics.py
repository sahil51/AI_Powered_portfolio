from __future__ import annotations

from dataclasses import dataclass, field

from application.context_builder.metrics import ContextMetrics


@dataclass
class ContextStatistics:
    build_count: int = 0
    avg_layers_per_build: float = 0.0
    avg_tokens_per_build: float = 0.0
    avg_build_time_ms: float = 0.0
    most_used_layers: list[str] = field(default_factory=list)
    compression_rate: float = 0.0
    cache_hit_rate: float = 0.0

    def update(self, metrics: ContextMetrics) -> None:
        self.build_count = metrics.total_builds
        self.avg_layers_per_build = metrics.avg_layers_per_build if hasattr(metrics, "avg_layers_per_build") else 0.0
        self.avg_tokens_per_build = metrics.avg_tokens_per_build
        self.avg_build_time_ms = metrics.avg_build_time_ms
        total = metrics.cache_hits + metrics.cache_misses
        self.cache_hit_rate = metrics.cache_hits / total if total > 0 else 0.0
