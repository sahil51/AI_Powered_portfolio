from __future__ import annotations

from collections import defaultdict
from typing import Any


class StatisticsCollector:
    def __init__(self) -> None:
        self._metrics: dict[str, list[float]] = defaultdict(list)
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}

    def record_latency(self, metric: str, value_ms: float) -> None:
        self._metrics[metric].append(value_ms)

    def increment(self, metric: str, count: int = 1) -> None:
        self._counters[metric] += count

    def set_gauge(self, metric: str, value: float) -> None:
        self._gauges[metric] = value

    def get_latency_stats(self, metric: str) -> dict[str, float]:
        values = self._metrics.get(metric, [])
        if not values:
            return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}
        sorted_values = sorted(values)
        n = len(sorted_values)
        return {
            "count": n,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / n,
            "p50": sorted_values[int(n * 0.5)],
            "p95": sorted_values[int(n * 0.95)],
            "p99": sorted_values[int(n * 0.99)],
        }

    def get_counter(self, metric: str) -> int:
        return self._counters.get(metric, 0)

    def get_gauge(self, metric: str) -> float:
        return self._gauges.get(metric, 0.0)

    def snapshot(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for metric in list(self._metrics.keys()):
            result[metric] = self.get_latency_stats(metric)
        for metric in list(self._counters.keys()):
            result[metric] = self._counters[metric]
        for metric in list(self._gauges.keys()):
            result[metric] = self._gauges[metric]
        return result

    def reset(self) -> None:
        self._metrics.clear()
        self._counters.clear()
        self._gauges.clear()
