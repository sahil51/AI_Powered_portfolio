from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from application.ai.interfaces import AIProvider

logger = logging.getLogger("ai_assistant")


class ProviderHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ProviderHealth:
    provider: str = ""
    status: ProviderHealthStatus = ProviderHealthStatus.UNKNOWN
    model_health: dict[str, bool] = field(default_factory=dict)
    latency_ms: float = 0.0
    last_check: float = 0.0
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status == ProviderHealthStatus.HEALTHY


class ProviderHealthChecker:
    def __init__(self) -> None:
        self._health_cache: dict[str, ProviderHealth] = {}

    async def check(self, provider: AIProvider) -> ProviderHealth:
        import time

        start = time.time()
        health = ProviderHealth(provider=provider.name, last_check=start)
        try:
            healthy = await provider.health_check()
            elapsed = (time.time() - start) * 1000
            health.latency_ms = elapsed
            if healthy:
                health.status = ProviderHealthStatus.HEALTHY
            else:
                health.status = ProviderHealthStatus.DEGRADED
            models = provider.list_models()
            for model in models:
                health.model_health[model.id] = model.healthy
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            health.latency_ms = elapsed
            health.status = ProviderHealthStatus.UNHEALTHY
            health.error = str(e)
            logger.warning("Health check failed for provider %s: %s", provider.name, e)
        self._health_cache[provider.name] = health
        return health

    def get_cached(self, provider_name: str) -> ProviderHealth | None:
        return self._health_cache.get(provider_name)

    async def check_all(self, providers: list[AIProvider]) -> list[ProviderHealth]:
        import asyncio

        results = await asyncio.gather(*[self.check(p) for p in providers], return_exceptions=True)
        output: list[ProviderHealth] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Health check exception for %s: %s", providers[i].name, result)
                output.append(
                    ProviderHealth(
                        provider=providers[i].name,
                        status=ProviderHealthStatus.UNHEALTHY,
                        error=str(result),
                    )
                )
            else:
                output.append(result)
        return output

    def clear_cache(self) -> None:
        self._health_cache.clear()
