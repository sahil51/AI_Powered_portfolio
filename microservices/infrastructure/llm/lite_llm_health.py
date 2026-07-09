from __future__ import annotations

from application.ai.health import ProviderHealth, ProviderHealthChecker, ProviderHealthStatus


class LiteLLMHealth:
    def __init__(self, provider_name: str = "litellm") -> None:
        self._provider_name = provider_name
        self._checker = ProviderHealthChecker()

    async def check(self, is_available: bool, latency_ms: float = 0.0, error: str | None = None) -> ProviderHealth:
        health = ProviderHealth(
            provider=self._provider_name,
            status=ProviderHealthStatus.HEALTHY if is_available else ProviderHealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
            error=error,
        )
        return health
