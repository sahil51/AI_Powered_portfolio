from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromptMetrics:
    total_loads: int = 0
    total_renders: int = 0
    total_registrations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    validation_errors: int = 0

    def record_load(self) -> None:
        self.total_loads += 1

    def record_render(self) -> None:
        self.total_renders += 1

    def record_registration(self) -> None:
        self.total_registrations += 1

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        self.cache_misses += 1

    def record_validation_error(self) -> None:
        self.validation_errors += 1

    def merge(self, other: PromptMetrics) -> None:
        self.total_loads += other.total_loads
        self.total_renders += other.total_renders
        self.total_registrations += other.total_registrations
        self.cache_hits += other.cache_hits
        self.cache_misses += other.cache_misses
        self.validation_errors += other.validation_errors
