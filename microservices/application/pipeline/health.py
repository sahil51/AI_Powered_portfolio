from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PipelineHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class PipelineHealth:
    status: PipelineHealthStatus = PipelineHealthStatus.UNKNOWN
    stage_health: dict[str, bool] = field(default_factory=dict)
    latency_ms: float = 0.0
    last_check: float = 0.0
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status == PipelineHealthStatus.HEALTHY
