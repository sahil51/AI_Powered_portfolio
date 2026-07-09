from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from application.workflow_client.models import WorkflowOperation, WorkflowResponseStatus


@dataclass
class WorkflowClientMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retry_count: int = 0
    timeout_count: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    requests_by_operation: dict[str, int] = field(default_factory=dict)
    requests_by_status: dict[str, int] = field(default_factory=dict)
    last_request_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowClientMetricsCollector:
    def __init__(self) -> None:
        self._metrics = WorkflowClientMetrics()
        self._start_time = time.time()

    @property
    def metrics(self) -> WorkflowClientMetrics:
        return self._metrics

    def record_request(
        self,
        operation: WorkflowOperation,
        status: WorkflowResponseStatus,
        latency_ms: float,
        retry: bool = False,
    ) -> None:
        self._metrics.total_requests += 1

        op_key = operation.value
        self._metrics.requests_by_operation[op_key] = (
            self._metrics.requests_by_operation.get(op_key, 0) + 1
        )

        status_key = status.value
        self._metrics.requests_by_status[status_key] = (
            self._metrics.requests_by_status.get(status_key, 0) + 1
        )

        if status == WorkflowResponseStatus.SUCCESS:
            self._metrics.successful_requests += 1
        else:
            self._metrics.failed_requests += 1

        if status == WorkflowResponseStatus.TIMEOUT:
            self._metrics.timeout_count += 1

        if retry:
            self._metrics.retry_count += 1

        self._metrics.total_latency_ms += latency_ms
        self._metrics.avg_latency_ms = (
            self._metrics.total_latency_ms / self._metrics.total_requests
        )
        self._metrics.max_latency_ms = max(self._metrics.max_latency_ms, latency_ms)
        self._metrics.min_latency_ms = (
            latency_ms
            if self._metrics.min_latency_ms == 0.0
            else min(self._metrics.min_latency_ms, latency_ms)
        )
        self._metrics.last_request_at = datetime.now(timezone.utc)

    def reset(self) -> None:
        self._metrics = WorkflowClientMetrics()
        self._start_time = time.time()
