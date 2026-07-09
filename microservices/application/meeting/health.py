from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from application.meeting.metrics import MeetingMetrics


class MeetingHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class MeetingHealth:
    status: MeetingHealthStatus = MeetingHealthStatus.HEALTHY
    total_meetings: int = 0
    completion_rate: float = 1.0
    failure_rate: float = 0.0
    avg_latency_ms: float = 0.0
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class MeetingHealthChecker:
    def __init__(
        self,
        max_avg_latency_ms: float = 10000.0,
        min_completion_rate: float = 0.7,
        max_failure_rate: float = 0.3,
        max_consecutive_errors: int = 5,
    ) -> None:
        self._max_avg_latency_ms = max_avg_latency_ms
        self._min_completion_rate = min_completion_rate
        self._max_failure_rate = max_failure_rate
        self._max_consecutive_errors = max_consecutive_errors
        self._consecutive_errors: list[str] = []

    async def check(self, metrics: MeetingMetrics | None = None) -> MeetingHealth:
        errors: list[str] = []
        status = MeetingHealthStatus.HEALTHY

        if metrics is not None and metrics.total_meetings > 0:
            failure_rate = metrics.failed_meetings / metrics.total_meetings
            if failure_rate > self._max_failure_rate:
                errors.append(
                    f"Failure rate {failure_rate:.2f} above threshold {self._max_failure_rate}"
                )
                status = MeetingHealthStatus.DEGRADED

            completion_rate = metrics.completed_meetings / metrics.total_meetings
            if completion_rate < self._min_completion_rate:
                errors.append(
                    f"Completion rate {completion_rate:.2f} below threshold {self._min_completion_rate}"
                )
                status = MeetingHealthStatus.DEGRADED

            if metrics.avg_latency_ms > self._max_avg_latency_ms:
                errors.append(
                    f"Avg latency {metrics.avg_latency_ms:.0f}ms above threshold {self._max_avg_latency_ms:.0f}ms"
                )
                status = MeetingHealthStatus.DEGRADED

        if len(self._consecutive_errors) >= self._max_consecutive_errors:
            errors.append(f"{len(self._consecutive_errors)} consecutive errors")
            status = MeetingHealthStatus.UNHEALTHY

        return MeetingHealth(
            status=status,
            total_meetings=metrics.total_meetings if metrics else 0,
            completion_rate=(
                metrics.completed_meetings / metrics.total_meetings
                if metrics and metrics.total_meetings > 0
                else 1.0
            ),
            failure_rate=(
                metrics.failed_meetings / metrics.total_meetings
                if metrics and metrics.total_meetings > 0
                else 0.0
            ),
            avg_latency_ms=metrics.avg_latency_ms if metrics else 0.0,
            last_checked=datetime.now(timezone.utc),
            errors=errors,
        )

    def record_error(self, error: str) -> None:
        self._consecutive_errors.append(error)
        if len(self._consecutive_errors) > self._max_consecutive_errors * 2:
            self._consecutive_errors = self._consecutive_errors[-self._max_consecutive_errors:]

    def record_success(self) -> None:
        self._consecutive_errors.clear()
