from __future__ import annotations

from application.embedding.health import EmbeddingHealth, EmbeddingHealthChecker, EmbeddingHealthStatus
from application.embedding.interfaces import EmbeddingProvider


class EmbeddingInfraHealth:
    def __init__(self, provider_name: str) -> None:
        self._provider_name = provider_name
        self._checker = EmbeddingHealthChecker()

    async def check(self, provider: EmbeddingProvider) -> EmbeddingHealth:
        try:
            healthy = provider.health_check()
            if healthy:
                self._checker.record_success()
                return self._checker.check()
            self._checker.record_failure(f"{self._provider_name} health check failed")
            result = self._checker.check()
            if result.status == EmbeddingHealthStatus.HEALTHY:
                result.status = EmbeddingHealthStatus.UNHEALTHY
            return result
        except Exception as e:
            self._checker.record_failure(str(e))
            result = self._checker.check()
            result.status = EmbeddingHealthStatus.UNHEALTHY
            result.errors.append(str(e))
            return result
