from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class MetricRecord:
    name: str
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    name: str
    latency_ms: float
    status: str  # "success" | "failure"
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadTestConfig:
    concurrent_users: int
    duration_seconds: int
    target_endpoints: list[str] = field(default_factory=list)


@dataclass
class StressTestResult:
    scenario_name: str
    success_rate: float
    max_concurrency: int
    failure_reason: Optional[str] = None
    graceful_degradation_active: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SLOThresholds:
    max_p95_latency_ms: float = 500.0
    max_p99_latency_ms: float = 1000.0
    min_throughput_rps: float = 10.0
    max_error_rate_pct: float = 1.0
    max_cpu_pct: float = 80.0
    max_memory_pct: float = 85.0


@dataclass
class PerformanceReport:
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    benchmarks: list[BenchmarkResult] = field(default_factory=list)
    validator_passed: bool = True
    errors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metrics_summary: dict[str, Any] = field(default_factory=dict)
