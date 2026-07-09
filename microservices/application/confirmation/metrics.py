from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.enums.confirmation import ConfirmationType


@dataclass
class ConfirmationMetrics:
    total_resolutions: int = 0
    successful_resolutions: int = 0
    failed_resolutions: int = 0
    resolutions_by_type: dict[str, int] = field(default_factory=dict)
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    ambiguity_count: int = 0
    correction_count: int = 0
    modification_count: int = 0
    cancellation_count: int = 0
    agent_readiness_count: int = 0
    last_resolved_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ConfirmationMetricsCollector:
    def __init__(self) -> None:
        self._metrics = ConfirmationMetrics()
        self._start_time = time.time()

    @property
    def metrics(self) -> ConfirmationMetrics:
        return self._metrics

    def record_resolution(
        self,
        confirmation_type: ConfirmationType,
        latency_ms: float,
        success: bool = True,
    ) -> None:
        self._metrics.total_resolutions += 1
        if success:
            self._metrics.successful_resolutions += 1
        else:
            self._metrics.failed_resolutions += 1

        type_key = confirmation_type.value
        self._metrics.resolutions_by_type[type_key] = (
            self._metrics.resolutions_by_type.get(type_key, 0) + 1
        )

        self._metrics.total_latency_ms += latency_ms
        self._metrics.avg_latency_ms = (
            self._metrics.total_latency_ms / self._metrics.total_resolutions
        )
        self._metrics.max_latency_ms = max(self._metrics.max_latency_ms, latency_ms)
        self._metrics.min_latency_ms = (
            latency_ms
            if self._metrics.min_latency_ms == 0.0
            else min(self._metrics.min_latency_ms, latency_ms)
        )

        if confirmation_type == ConfirmationType.AMBIGUOUS:
            self._metrics.ambiguity_count += 1
        elif confirmation_type == ConfirmationType.CORRECTION:
            self._metrics.correction_count += 1
        elif confirmation_type == ConfirmationType.MODIFICATION:
            self._metrics.modification_count += 1
        elif confirmation_type == ConfirmationType.CANCELLATION:
            self._metrics.cancellation_count += 1

        self._metrics.last_resolved_at = datetime.now(timezone.utc)

    def record_agent_readiness(self) -> None:
        self._metrics.agent_readiness_count += 1

    def reset(self) -> None:
        self._metrics = ConfirmationMetrics()
        self._start_time = time.time()
