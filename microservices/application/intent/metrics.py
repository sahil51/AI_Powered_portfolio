from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.enums.intent import IntentType


@dataclass
class IntentMetrics:
    total_classifications: int = 0
    successful_classifications: int = 0
    failed_classifications: int = 0
    classifications_by_intent: dict[str, int] = field(default_factory=dict)
    classifications_by_confidence: dict[str, int] = field(default_factory=dict)
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    entity_extractions: int = 0
    entity_extraction_errors: int = 0
    clarifications_requested: int = 0
    fallbacks_triggered: int = 0
    auto_accepted: int = 0
    last_classified_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class IntentMetricsCollector:
    def __init__(self) -> None:
        self._metrics = IntentMetrics()
        self._start_time = time.time()

    @property
    def metrics(self) -> IntentMetrics:
        return self._metrics

    def record_classification(
        self,
        intent: IntentType,
        confidence: float,
        latency_ms: float,
        success: bool = True,
    ) -> None:
        self._metrics.total_classifications += 1
        if success:
            self._metrics.successful_classifications += 1
        else:
            self._metrics.failed_classifications += 1

        intent_key = intent.value
        self._metrics.classifications_by_intent[intent_key] = (
            self._metrics.classifications_by_intent.get(intent_key, 0) + 1
        )

        level = self._confidence_level(confidence)
        self._metrics.classifications_by_confidence[level] = (
            self._metrics.classifications_by_confidence.get(level, 0) + 1
        )

        self._metrics.total_latency_ms += latency_ms
        self._metrics.avg_latency_ms = (
            self._metrics.total_latency_ms / self._metrics.total_classifications
        )
        self._metrics.max_latency_ms = max(self._metrics.max_latency_ms, latency_ms)
        self._metrics.min_latency_ms = (
            latency_ms
            if self._metrics.min_latency_ms == 0.0
            else min(self._metrics.min_latency_ms, latency_ms)
        )
        self._metrics.last_classified_at = datetime.now(timezone.utc)

    def record_entity_extraction(self, success: bool = True) -> None:
        self._metrics.entity_extractions += 1
        if not success:
            self._metrics.entity_extraction_errors += 1

    def record_clarification(self) -> None:
        self._metrics.clarifications_requested += 1

    def record_fallback(self) -> None:
        self._metrics.fallbacks_triggered += 1

    def record_auto_accept(self) -> None:
        self._metrics.auto_accepted += 1

    def reset(self) -> None:
        self._metrics = IntentMetrics()
        self._start_time = time.time()

    def _confidence_level(self, score: float) -> str:
        if score >= 0.85:
            return "high"
        if score >= 0.60:
            return "medium"
        if score >= 0.30:
            return "low"
        return "uncertain"
