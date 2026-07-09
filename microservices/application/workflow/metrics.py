from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class WorkflowMetrics:
    workflow_id: str = ""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    paused_executions: int = 0
    cancelled_executions: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    retry_count: int = 0
    recovery_count: int = 0
    checkpoint_count: int = 0
    last_execution_time: float = 0.0
    state_transitions: dict[str, int] = field(default_factory=dict)

    @property
    def avg_latency_ms(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.total_latency_ms / self.total_executions

    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 1.0
        return self.successful_executions / self.total_executions

    @property
    def failure_rate(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.failed_executions / self.total_executions

    def merge(self, other: WorkflowMetrics) -> None:
        self.total_executions += other.total_executions
        self.successful_executions += other.successful_executions
        self.failed_executions += other.failed_executions
        self.paused_executions += other.paused_executions
        self.cancelled_executions += other.cancelled_executions
        self.total_latency_ms += other.total_latency_ms
        if other.min_latency_ms > 0:
            self.min_latency_ms = (
                min(self.min_latency_ms, other.min_latency_ms)
                if self.min_latency_ms > 0
                else other.min_latency_ms
            )
        self.max_latency_ms = max(self.max_latency_ms, other.max_latency_ms)
        self.retry_count += other.retry_count
        self.recovery_count += other.recovery_count
        self.checkpoint_count += other.checkpoint_count
        if other.last_execution_time > self.last_execution_time:
            self.last_execution_time = other.last_execution_time
        for state, count in other.state_transitions.items():
            self.state_transitions[state] = self.state_transitions.get(state, 0) + count


@dataclass
class WorkflowEngineMetrics:
    total_engines: int = 0
    registered_workflows: int = 0
    total_executions: int = 0
    total_errors: int = 0
    total_retries: int = 0
    total_recoveries: int = 0
    total_checkpoints: int = 0
    uptime_seconds: float = 0.0


class WorkflowMetricsCollector:
    def __init__(self) -> None:
        self._workflow_metrics: dict[str, WorkflowMetrics] = {}
        self._engine_metrics: WorkflowEngineMetrics = WorkflowEngineMetrics()
        self._start_time: float = time.time()

    @property
    def engine(self) -> WorkflowEngineMetrics:
        self._engine_metrics.uptime_seconds = time.time() - self._start_time
        return self._engine_metrics

    def record_execution(
        self,
        workflow_id: str,
        success: bool,
        latency_ms: float,
    ) -> None:
        if workflow_id not in self._workflow_metrics:
            self._workflow_metrics[workflow_id] = WorkflowMetrics(workflow_id=workflow_id)
        metrics = self._workflow_metrics[workflow_id]
        metrics.total_executions += 1
        metrics.last_execution_time = time.time()
        if success:
            metrics.successful_executions += 1
        else:
            metrics.failed_executions += 1
            self._engine_metrics.total_errors += 1
        metrics.total_latency_ms += latency_ms
        if metrics.min_latency_ms == 0 or latency_ms < metrics.min_latency_ms:
            metrics.min_latency_ms = latency_ms
        if latency_ms > metrics.max_latency_ms:
            metrics.max_latency_ms = latency_ms
        self._engine_metrics.total_executions += 1

    def record_retry(self, workflow_id: str) -> None:
        if workflow_id not in self._workflow_metrics:
            self._workflow_metrics[workflow_id] = WorkflowMetrics(workflow_id=workflow_id)
        self._workflow_metrics[workflow_id].retry_count += 1
        self._engine_metrics.total_retries += 1

    def record_recovery(self, workflow_id: str) -> None:
        if workflow_id not in self._workflow_metrics:
            self._workflow_metrics[workflow_id] = WorkflowMetrics(workflow_id=workflow_id)
        self._workflow_metrics[workflow_id].recovery_count += 1
        self._engine_metrics.total_recoveries += 1

    def record_checkpoint(self, workflow_id: str) -> None:
        if workflow_id not in self._workflow_metrics:
            self._workflow_metrics[workflow_id] = WorkflowMetrics(workflow_id=workflow_id)
        self._workflow_metrics[workflow_id].checkpoint_count += 1
        self._engine_metrics.total_checkpoints += 1

    def get_metrics(self, workflow_id: str | None = None) -> WorkflowMetrics | dict[str, WorkflowMetrics]:
        if workflow_id:
            return self._workflow_metrics.get(workflow_id, WorkflowMetrics(workflow_id=workflow_id))
        return dict(self._workflow_metrics)

    def reset(self, workflow_id: str | None = None) -> None:
        if workflow_id:
            self._workflow_metrics.pop(workflow_id, None)
        else:
            self._workflow_metrics.clear()
            self._engine_metrics = WorkflowEngineMetrics()
            self._start_time = time.time()
