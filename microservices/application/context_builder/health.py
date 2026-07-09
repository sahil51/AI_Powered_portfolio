from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContextHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ContextHealth:
    status: ContextHealthStatus = ContextHealthStatus.HEALTHY
    layer_count: int = 0
    enabled_layer_count: int = 0
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
