from __future__ import annotations

from abc import abstractmethod

from application.embedding.exceptions import (
    EmbeddingConfigurationError,
    EmbeddingProviderError,
)
from application.embedding.interfaces import EmbeddingProvider
from application.embedding.models import (
    EmbeddingConfiguration,
    EmbeddingProviderType,
    EmbeddingRequest,
    EmbeddingResponse,
)
from application.embedding.validator import EmbeddingValidator


class BaseEmbeddingProvider(EmbeddingProvider):
    def __init__(self, config: EmbeddingConfiguration) -> None:
        self._config = config
        self._validator = EmbeddingValidator()

    @property
    @abstractmethod
    def provider_type(self) -> EmbeddingProviderType:
        ...

    @property
    def configuration(self) -> EmbeddingConfiguration:
        return self._config

    def validate_configuration(self, config: EmbeddingConfiguration) -> bool:
        try:
            self._validator.validate_configuration(config)
            return True
        except EmbeddingConfigurationError:
            return False

    def health_check(self) -> bool:
        try:
            return self._perform_health_check()
        except Exception:
            return False

    @abstractmethod
    def generate(self, request: EmbeddingRequest) -> EmbeddingResponse:
        ...

    @abstractmethod
    def generate_batch(self, requests: list[EmbeddingRequest]) -> list[EmbeddingResponse]:
        ...

    def _perform_health_check(self) -> bool:
        try:
            return self._config.model != ""
        except Exception:
            return False

    def _validate_embedding_response(
        self,
        request: EmbeddingRequest,
        response: EmbeddingResponse,
    ) -> None:
        if not response.embedding:
            raise EmbeddingProviderError(
                f"Provider returned empty embedding for chunk {request.chunk_id}"
            )
        if response.dimension <= 0:
            raise EmbeddingProviderError(
                f"Invalid embedding dimension {response.dimension} for chunk {request.chunk_id}"
            )
