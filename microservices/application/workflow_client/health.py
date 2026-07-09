from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from application.workflow_client.metrics import WorkflowClientMetrics


class WorkflowClientHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class WorkflowClientHealth:
    status: WorkflowClientHealthStatus = WorkflowClientHealthStatus.HEALTHY
    total_requests: int = 0
    success_rate: float = 1.0
    avg_latency_ms: float = 0.0
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowClientHealthChecker:
    def __init__(
        self,
        max_avg_latency_ms: float = 5000.0,
        min_success_rate: float = 0.8,
        max_consecutive_failures: int = 5,
    ) -> None:
        self._max_avg_latency_ms = max_avg_latency_ms
        self._min_success_rate = min_success_rate
        self._max_consecutive_failures = max_consecutive_failures
        self._consecutive_failures: list[str] = []

    async def check(self, metrics: WorkflowClientMetrics | None = None) -> WorkflowClientHealth:
        errors: list[str] = []
        status = WorkflowClientHealthStatus.HEALTHY

        if metrics is not None and metrics.total_requests > 0:
            success_rate = metrics.successful_requests / metrics.total_requests
            if success_rate < self._min_success_rate:
                errors.append(
                    f"Success rate {success_rate:.2f} below threshold {self._min_success_rate}"
                )
                status = WorkflowClientHealthStatus.DEGRADED

            if metrics.avg_latency_ms > self._max_avg_latency_ms:
                errors.append(
                    f"Avg latency {metrics.avg_latency_ms:.0f}ms above threshold {self._max_avg_latency_ms:.0f}ms"
                )
                status = WorkflowClientHealthStatus.DEGRADED

        if len(self._consecutive_failures) >= self._max_consecutive_failures:
            errors.append(f"{len(self._consecutive_failures)} consecutive failures")
            status = WorkflowClientHealthStatus.UNHEALTHY

        return WorkflowClientHealth(
            status=status,
            total_requests=metrics.total_requests if metrics else 0,
            success_rate=(
                metrics.successful_requests / metrics.total_requests
                if metrics and metrics.total_requests > 0
                else 1.0
            ),
            avg_latency_ms=metrics.avg_latency_ms if metrics else 0.0,
            last_checked=datetime.now(timezone.utc),
            errors=errors,
        )

    def record_failure(self, error: str) -> None:
        self._consecutive_failures.append(error)
        if len(self._consecutive_failures) > self._max_consecutive_failures * 2:
            self._consecutive_failures = self._consecutive_failures[
                -self._max_consecutive_failures:
            ]

    def record_success(self) -> None:
        self._consecutive_failures.clear()
