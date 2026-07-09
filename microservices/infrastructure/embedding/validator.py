from __future__ import annotations

from application.embedding.exceptions import EmbeddingConfigurationError
from application.embedding.models import EmbeddingConfiguration, EmbeddingRequest
from application.embedding.validator import EmbeddingValidator
from infrastructure.embedding.config import EmbeddingClientConfig


class EmbeddingInfraValidator:
    def __init__(self, client_config: EmbeddingClientConfig) -> None:
        self._validator = EmbeddingValidator()
        self._client_config = client_config

    def validate_request(self, request: EmbeddingRequest) -> None:
        self._validator.validate_request(request)

    def validate_configuration(self, config: EmbeddingConfiguration) -> None:
        self._validator.validate_configuration(config)
        provider_key = config.provider.value
        if provider_key not in self._client_config.api_keys:
            raise EmbeddingConfigurationError(
                f"No API key configured for provider: {config.provider.value}"
            )
