from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from application.intent.metrics import IntentMetrics


class IntentHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class IntentHealth:
    status: IntentHealthStatus = IntentHealthStatus.HEALTHY
    total_classifications: int = 0
    success_rate: float = 1.0
    avg_latency_ms: float = 0.0
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class IntentHealthChecker:
    def __init__(
        self,
        max_avg_latency_ms: float = 5000.0,
        min_success_rate: float = 0.8,
        max_consecutive_errors: int = 5,
    ) -> None:
        self._max_avg_latency_ms = max_avg_latency_ms
        self._min_success_rate = min_success_rate
        self._max_consecutive_errors = max_consecutive_errors
        self._consecutive_errors: list[str] = []

    async def check(self, metrics: IntentMetrics | None = None) -> IntentHealth:
        if metrics is None:
            return IntentHealth(status=IntentHealthStatus.HEALTHY)

        errors: list[str] = []
        status = IntentHealthStatus.HEALTHY

        if metrics.total_classifications > 0:
            success_rate = metrics.successful_classifications / metrics.total_classifications
            if success_rate < self._min_success_rate:
                errors.append(f"Success rate {success_rate:.2f} below threshold {self._min_success_rate}")
                status = IntentHealthStatus.DEGRADED

            if metrics.avg_latency_ms > self._max_avg_latency_ms:
                errors.append(
                    f"Avg latency {metrics.avg_latency_ms:.0f}ms above threshold {self._max_avg_latency_ms:.0f}ms"
                )
                status = IntentHealthStatus.DEGRADED

        if len(self._consecutive_errors) >= self._max_consecutive_errors:
            errors.append(f"{len(self._consecutive_errors)} consecutive errors detected")
            status = IntentHealthStatus.UNHEALTHY

        return IntentHealth(
            status=status,
            total_classifications=metrics.total_classifications,
            success_rate=(
                metrics.successful_classifications / metrics.total_classifications
                if metrics.total_classifications > 0
                else 1.0
            ),
            avg_latency_ms=metrics.avg_latency_ms,
            last_checked=datetime.now(timezone.utc),
            errors=errors,
        )

    def record_error(self, error: str) -> None:
        self._consecutive_errors.append(error)
        if len(self._consecutive_errors) > self._max_consecutive_errors * 2:
            self._consecutive_errors = self._consecutive_errors[-self._max_consecutive_errors:]

    def record_success(self) -> None:
        self._consecutive_errors.clear()
