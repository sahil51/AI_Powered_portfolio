from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderConfiguration:
    name: str = ""
    api_key: str = ""
    base_url: str = ""
    default_model: str = ""
    models: list[str] = field(default_factory=list)
    timeout: float = 30.0
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_seconds: int = 60
    rate_limit_per_minute: int = 30
    fallback_models: list[str] = field(default_factory=list)
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
