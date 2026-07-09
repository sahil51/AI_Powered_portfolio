from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from config.settings import settings


class SamplingStrategy(Enum):
    ALWAYS = "always"
    NEVER = "never"
    PROBABILISTIC = "probabilistic"
    RATE_LIMITED = "rate_limited"


@dataclass
class TelemetryConfiguration:
    service_name: str = settings.app_name
    service_version: str = settings.app_version
    environment: str = settings.environment
    tracing_enabled: bool = True
    metrics_enabled: bool = True
    logging_enabled: bool = True
    sampling_strategy: SamplingStrategy = SamplingStrategy.ALWAYS
    sampling_rate: float = 1.0
    max_trace_batch_size: int = 100
    export_interval_seconds: int = 10
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    otlp_endpoint: str = ""
    otlp_enabled: bool = False
    sentry_enabled: bool = bool(settings.sentry_dsn)
    sentry_dsn: str = settings.sentry_dsn
    baggage_keys: list[str] = field(default_factory=lambda: ["user_id", "tenant_id", "conversation_id"])
    attributes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "service_version": self.service_version,
            "environment": self.environment,
            "tracing_enabled": self.tracing_enabled,
            "metrics_enabled": self.metrics_enabled,
            "logging_enabled": self.logging_enabled,
            "sampling_strategy": self.sampling_strategy.value,
            "sampling_rate": self.sampling_rate,
            "prometheus_enabled": self.prometheus_enabled,
            "prometheus_port": self.prometheus_port,
            "otlp_enabled": self.otlp_enabled,
            "sentry_enabled": self.sentry_enabled,
            "baggage_keys": self.baggage_keys,
        }
