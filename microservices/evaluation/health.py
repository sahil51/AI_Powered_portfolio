from __future__ import annotations

import time
from typing import Any

from evaluation.models import EvaluationHealth, EvaluationStatus


class EvaluationHealthChecker:
    def __init__(self) -> None:
        self._health = EvaluationHealth()

    @property
    def health(self) -> EvaluationHealth:
        return self._health

    def record_run(self, status: EvaluationStatus) -> None:
        self._health.last_run_timestamp = time.time()
        self._health.last_run_status = status.value

    def record_error(self, error: str) -> None:
        self._health.errors.append(error)
        self._health.healthy = False

    def set_datasets_loaded(self, count: int) -> None:
        self._health.datasets_loaded = count

    def set_evaluators_registered(self, count: int) -> None:
        self._health.evaluators_registered = count

    def check(self) -> dict[str, Any]:
        return {
            "healthy": self._health.healthy,
            "datasets_loaded": self._health.datasets_loaded,
            "evaluators_registered": self._health.evaluators_registered,
            "last_run_timestamp": self._health.last_run_timestamp,
            "last_run_status": self._health.last_run_status,
            "errors": self._health.errors,
        }

    def reset(self) -> None:
        self._health = EvaluationHealth()
