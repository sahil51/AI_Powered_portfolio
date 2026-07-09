from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContextMetrics:
    total_builds: int = 0
    total_layers_built: int = 0
    total_tokens_processed: int = 0
    total_build_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    compression_applied: int = 0

    @property
    def avg_build_time_ms(self) -> float:
        if self.total_builds == 0:
            return 0.0
        return self.total_build_time_ms / self.total_builds

    @property
    def avg_tokens_per_build(self) -> float:
        if self.total_builds == 0:
            return 0.0
        return self.total_tokens_processed / self.total_builds

    def record_build(self, layer_count: int, tokens: int, elapsed_ms: float) -> None:
        self.total_builds += 1
        self.total_layers_built += layer_count
        self.total_tokens_processed += tokens
        self.total_build_time_ms += elapsed_ms

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        self.cache_misses += 1

    def record_compression(self) -> None:
        self.compression_applied += 1

    def merge(self, other: ContextMetrics) -> None:
        self.total_builds += other.total_builds
        self.total_layers_built += other.total_layers_built
        self.total_tokens_processed += other.total_tokens_processed
        self.total_build_time_ms += other.total_build_time_ms
        self.cache_hits += other.cache_hits
        self.cache_misses += other.cache_misses
        self.compression_applied += other.compression_applied
