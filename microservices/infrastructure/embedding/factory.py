from __future__ import annotations

from application.embedding.exceptions import EmbeddingConfigurationError
from application.embedding.interfaces import EmbeddingProvider
from application.embedding.models import EmbeddingConfiguration, EmbeddingProviderType
from infrastructure.embedding.config import EmbeddingClientConfig
from infrastructure.embedding.providers.gemini import GeminiEmbeddingProvider
from infrastructure.embedding.registry import ProviderRegistry


class ProviderFactory:
    @staticmethod
    def create(
        provider_type: EmbeddingProviderType,
        config: EmbeddingConfiguration | None = None,
        client_config: EmbeddingClientConfig | None = None,
    ) -> EmbeddingProvider:
        client_config = client_config or EmbeddingClientConfig.from_settings()
        resolved_config = config or EmbeddingConfiguration(
            provider=provider_type,
            model=client_config.default_model or "text-embedding-004",
        )
        if provider_type == EmbeddingProviderType.GEMINI:
            return GeminiEmbeddingProvider(resolved_config, client_config)
        raise EmbeddingConfigurationError(f"Unsupported provider type: {provider_type}")

    @staticmethod
    def register_all(registry: ProviderRegistry, config: EmbeddingConfiguration) -> None:
        client_config = EmbeddingClientConfig.from_settings()
        for ptype in EmbeddingProviderType:
            if ptype == EmbeddingProviderType.CUSTOM:
                continue
            try:
                provider = ProviderFactory.create(ptype, config, client_config)
                registry.register(ptype, provider)
            except EmbeddingConfigurationError:
                pass
