from __future__ import annotations

from application.embedding.health import EmbeddingHealth, EmbeddingHealthChecker, EmbeddingHealthStatus
from application.embedding.interfaces import EmbeddingProvider
from application.embedding.models import EmbeddingProviderType


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[EmbeddingProviderType, EmbeddingProvider] = {}
        self._health_checker = EmbeddingHealthChecker()

    def register(self, provider_type: EmbeddingProviderType, provider: EmbeddingProvider) -> None:
        self._providers[provider_type] = provider

    def get(self, provider_type: EmbeddingProviderType) -> EmbeddingProvider | None:
        return self._providers.get(provider_type)

    def list_providers(self) -> dict[EmbeddingProviderType, EmbeddingProvider]:
        return dict(self._providers)

    def health_of_all(self) -> dict[EmbeddingProviderType, EmbeddingHealth]:
        result: dict[EmbeddingProviderType, EmbeddingHealth] = {}
        for ptype, provider in self._providers.items():
            try:
                healthy = provider.health_check()
                result[ptype] = EmbeddingHealth(
                    status=EmbeddingHealthStatus.HEALTHY if healthy else EmbeddingHealthStatus.UNHEALTHY,
                )
            except Exception as e:
                result[ptype] = EmbeddingHealth(
                    status=EmbeddingHealthStatus.UNHEALTHY,
                    errors=[str(e)],
                )
        return result

    @property
    def count(self) -> int:
        return len(self._providers)
