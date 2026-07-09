from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class KnowledgeContextHealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class KnowledgeContextHealthData:
    status: KnowledgeContextHealthStatus = KnowledgeContextHealthStatus.HEALTHY
    total_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    last_request_at: float = 0.0
    last_error: str = ""


class KnowledgeContextHealthChecker:
    def __init__(self) -> None:
        self._health = KnowledgeContextHealthData()
        self._DEGRADE_THRESHOLD = 5
        self._UNHEALTHY_THRESHOLD = 20

    def record_success(self) -> None:
        self._health.total_requests += 1
        self._health.consecutive_failures = 0
        self._health.last_request_at = time.time()
        self._health.status = KnowledgeContextHealthStatus.HEALTHY

    def record_failure(self, error: str = "") -> None:
        self._health.total_requests += 1
        self._health.failed_requests += 1
        self._health.consecutive_failures += 1
        self._health.last_error = error
        self._health.last_request_at = time.time()

        if self._health.consecutive_failures >= self._UNHEALTHY_THRESHOLD:
            self._health.status = KnowledgeContextHealthStatus.UNHEALTHY
        elif self._health.consecutive_failures >= self._DEGRADE_THRESHOLD:
            if self._health.status != KnowledgeContextHealthStatus.UNHEALTHY:
                self._health.status = KnowledgeContextHealthStatus.DEGRADED

    def check(self) -> dict[str, Any]:
        return {
            "status": self._health.status.value,
            "total_requests": self._health.total_requests,
            "failed_requests": self._health.failed_requests,
            "consecutive_failures": self._health.consecutive_failures,
            "success_rate": self._calculate_success_rate(),
            "last_request_at": self._health.last_request_at,
            "last_error": self._health.last_error,
        }

    def _calculate_success_rate(self) -> float:
        if self._health.total_requests == 0:
            return 1.0
        return 1.0 - (self._health.failed_requests / self._health.total_requests)

    def reset(self) -> None:
        self._health = KnowledgeContextHealthData()
