from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class KnowledgeImportHealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class KnowledgeImportHealth:
    status: KnowledgeImportHealthStatus = KnowledgeImportHealthStatus.HEALTHY
    total_imports: int = 0
    failed_imports: int = 0
    consecutive_failures: int = 0
    last_import_at: float = 0.0
    last_error: str = ""
    degraded_at: float = 0.0


class KnowledgeImportHealthChecker:
    def __init__(self) -> None:
        self._health = KnowledgeImportHealth()
        self._DEGRADE_THRESHOLD = 5
        self._UNHEALTHY_THRESHOLD = 20

    def record_success(self) -> None:
        self._health.total_imports += 1
        self._health.consecutive_failures = 0
        self._health.last_import_at = time.time()
        self._health.status = KnowledgeImportHealthStatus.HEALTHY

    def record_failure(self, error: str = "") -> None:
        self._health.total_imports += 1
        self._health.failed_imports += 1
        self._health.consecutive_failures += 1
        self._health.last_error = error

        if self._health.consecutive_failures >= self._UNHEALTHY_THRESHOLD:
            self._health.status = KnowledgeImportHealthStatus.UNHEALTHY
        elif self._health.consecutive_failures >= self._DEGRADE_THRESHOLD:
            if self._health.status != KnowledgeImportHealthStatus.UNHEALTHY:
                self._health.status = KnowledgeImportHealthStatus.DEGRADED
                self._health.degraded_at = time.time()

    def check(self) -> dict[str, Any]:
        return {
            "status": self._health.status.value,
            "total_imports": self._health.total_imports,
            "failed_imports": self._health.failed_imports,
            "consecutive_failures": self._health.consecutive_failures,
            "success_rate": self._calculate_success_rate(),
            "last_import_at": self._health.last_import_at,
            "last_error": self._health.last_error,
            "degraded_at": self._health.degraded_at,
        }

    def _calculate_success_rate(self) -> float:
        if self._health.total_imports == 0:
            return 1.0
        return 1.0 - (self._health.failed_imports / self._health.total_imports)

    def reset(self) -> None:
        self._health = KnowledgeImportHealth()
