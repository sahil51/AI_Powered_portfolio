from __future__ import annotations

from dataclasses import dataclass, field

from application.prompts.metrics import PromptMetrics


@dataclass
class PromptStatistics:
    total_prompts: int = 0
    active_prompts: int = 0
    deprecated_prompts: int = 0
    total_renders: int = 0
    avg_render_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    categories: list[str] = field(default_factory=list)

    def update(self, metrics: PromptMetrics) -> None:
        self.total_renders = metrics.total_renders
        total = metrics.cache_hits + metrics.cache_misses
        self.cache_hit_rate = metrics.cache_hits / total if total > 0 else 0.0
