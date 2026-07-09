from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PromptHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class PromptHealth:
    status: PromptHealthStatus = PromptHealthStatus.HEALTHY
    registry_count: int = 0
    cache_available: bool = False
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
