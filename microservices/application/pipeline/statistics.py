from __future__ import annotations

from dataclasses import dataclass

from application.pipeline.metrics import PipelineMetrics


@dataclass
class PipelineStatistics:
    total_pipelines: int = 0
    avg_latency_ms: float = 0.0
    avg_tokens_per_pipeline: float = 0.0
    avg_cost_per_pipeline: float = 0.0
    success_rate: float = 1.0
    failure_rate: float = 0.0
    avg_stages_per_pipeline: float = 0.0
    slowest_stage: str = ""
    slowest_stage_ms: float = 0.0

    def update(self, metrics: PipelineMetrics) -> None:
        self.total_pipelines = metrics.total_pipelines
        self.avg_latency_ms = metrics.avg_latency_ms
        self.success_rate = metrics.success_rate
        self.failure_rate = metrics.failure_rate
        if metrics.total_pipelines > 0:
            self.avg_tokens_per_pipeline = metrics.total_tokens / metrics.total_pipelines
            self.avg_cost_per_pipeline = metrics.total_cost / metrics.total_pipelines
        if metrics.stage_latency:
            self.slowest_stage = max(metrics.stage_latency, key=metrics.stage_latency.get)
            self.slowest_stage_ms = metrics.stage_latency[self.slowest_stage]
