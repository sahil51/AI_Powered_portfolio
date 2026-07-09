from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.enums.intent import IntentType


@dataclass
class IntentStatisticsData:
    total_classified: int = 0
    by_intent: dict[str, int] = field(default_factory=dict)
    by_confidence_level: dict[str, int] = field(default_factory=dict)
    by_hour: dict[int, int] = field(default_factory=dict)
    by_day: dict[str, int] = field(default_factory=dict)
    avg_confidence: float = 0.0
    avg_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    top_intents: list[tuple[str, int]] = field(default_factory=list)
    session_count: int = 0
    user_count: int = 0
    unique_users: set[str] = field(default_factory=set)
    unique_sessions: set[str] = field(default_factory=set)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class IntentStatistics:
    def __init__(self) -> None:
        self._data = IntentStatisticsData()

    @property
    def data(self) -> IntentStatisticsData:
        return self._data

    def record(
        self,
        intent: IntentType,
        confidence: float,
        latency_ms: float,
        user_id: str,
        session_id: str,
    ) -> None:
        self._data.total_classified += 1
        key = intent.value
        self._data.by_intent[key] = self._data.by_intent.get(key, 0) + 1

        level = self._confidence_level(confidence)
        self._data.by_confidence_level[level] = (
            self._data.by_confidence_level.get(level, 0) + 1
        )

        hour = datetime.now(timezone.utc).hour
        self._data.by_hour[hour] = self._data.by_hour.get(hour, 0) + 1

        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._data.by_day[day] = self._data.by_day.get(day, 0) + 1

        self._data.total_latency_ms += latency_ms
        self._data.avg_latency_ms = (
            self._data.total_latency_ms / self._data.total_classified
        )
        self._data.avg_confidence = (
            (self._data.avg_confidence * (self._data.total_classified - 1) + confidence)
            / self._data.total_classified
        )

        self._data.unique_users.add(user_id)
        self._data.unique_sessions.add(session_id)
        self._data.user_count = len(self._data.unique_users)
        self._data.session_count = len(self._data.unique_sessions)

        sorted_intents = sorted(
            self._data.by_intent.items(), key=lambda x: x[1], reverse=True
        )
        self._data.top_intents = sorted_intents[:10]
        self._data.last_updated = datetime.now(timezone.utc)

    def reset(self) -> None:
        self._data = IntentStatisticsData()

    def _confidence_level(self, score: float) -> str:
        if score >= 0.85:
            return "high"
        if score >= 0.60:
            return "medium"
        if score >= 0.30:
            return "low"
        return "uncertain"
