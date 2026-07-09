from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MeetingMetrics:
    total_meetings: int = 0
    completed_meetings: int = 0
    cancelled_meetings: int = 0
    failed_meetings: int = 0
    submitted_meetings: int = 0
    total_fields_collected: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    correction_count: int = 0
    reschedule_count: int = 0
    cancellation_count: int = 0
    last_activity_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class MeetingMetricsCollector:
    def __init__(self) -> None:
        self._metrics = MeetingMetrics()
        self._start_time = time.time()

    @property
    def metrics(self) -> MeetingMetrics:
        return self._metrics

    def record_meeting_created(self) -> None:
        self._metrics.total_meetings += 1

    def record_meeting_completed(self) -> None:
        self._metrics.completed_meetings += 1

    def record_meeting_cancelled(self) -> None:
        self._metrics.cancelled_meetings += 1

    def record_meeting_failed(self) -> None:
        self._metrics.failed_meetings += 1

    def record_meeting_submitted(self) -> None:
        self._metrics.submitted_meetings += 1

    def record_field_collected(self) -> None:
        self._metrics.total_fields_collected += 1

    def record_latency(self, latency_ms: float) -> None:
        self._metrics.total_latency_ms += latency_ms
        self._metrics.avg_latency_ms = (
            self._metrics.total_latency_ms / max(self._metrics.total_meetings, 1)
        )
        self._metrics.max_latency_ms = max(self._metrics.max_latency_ms, latency_ms)
        self._metrics.min_latency_ms = (
            latency_ms
            if self._metrics.min_latency_ms == 0.0
            else min(self._metrics.min_latency_ms, latency_ms)
        )

    def record_correction(self) -> None:
        self._metrics.correction_count += 1

    def record_reschedule(self) -> None:
        self._metrics.reschedule_count += 1

    def record_cancellation(self) -> None:
        self._metrics.cancellation_count += 1

    def reset(self) -> None:
        self._metrics = MeetingMetrics()
        self._start_time = time.time()
