from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PipelineMetrics:
    total_pipelines: int = 0
    successful_pipelines: int = 0
    failed_pipelines: int = 0
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    stage_latency: dict[str, float] = field(default_factory=dict)
    warnings_count: int = 0
    last_pipeline_time: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        if self.total_pipelines == 0:
            return 0.0
        return self.total_latency_ms / self.total_pipelines

    @property
    def success_rate(self) -> float:
        if self.total_pipelines == 0:
            return 1.0
        return self.successful_pipelines / self.total_pipelines

    @property
    def failure_rate(self) -> float:
        if self.total_pipelines == 0:
            return 0.0
        return self.failed_pipelines / self.total_pipelines

    def record_pipeline(
        self, success: bool, latency_ms: float, tokens: int = 0, cost: float = 0.0, warnings: int = 0,
    ) -> None:
        self.total_pipelines += 1
        if success:
            self.successful_pipelines += 1
        else:
            self.failed_pipelines += 1
        self.total_latency_ms += latency_ms
        self.total_tokens += tokens
        self.total_cost += cost
        self.warnings_count += warnings
        import time
        self.last_pipeline_time = time.time()

    def record_stage(self, stage: str, latency_ms: float) -> None:
        self.stage_latency[stage] = self.stage_latency.get(stage, 0.0) + latency_ms

    def merge(self, other: PipelineMetrics) -> None:
        self.total_pipelines += other.total_pipelines
        self.successful_pipelines += other.successful_pipelines
        self.failed_pipelines += other.failed_pipelines
        self.total_latency_ms += other.total_latency_ms
        self.total_tokens += other.total_tokens
        self.total_cost += other.total_cost
        self.warnings_count += other.warnings_count
        for stage, lat in other.stage_latency.items():
            self.stage_latency[stage] = self.stage_latency.get(stage, 0.0) + lat
