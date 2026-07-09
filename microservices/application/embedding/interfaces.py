from __future__ import annotations

from abc import ABC, abstractmethod

from application.embedding.models import (
    EmbeddingConfiguration,
    EmbeddingProviderType,
    EmbeddingRequest,
    EmbeddingResponse,
)


class EmbeddingProvider(ABC):
    @abstractmethod
    def generate(self, request: EmbeddingRequest) -> EmbeddingResponse:
        ...

    @abstractmethod
    def generate_batch(self, requests: list[EmbeddingRequest]) -> list[EmbeddingResponse]:
        ...

    @abstractmethod
    def validate_configuration(self, config: EmbeddingConfiguration) -> bool:
        ...

    @abstractmethod
    def health_check(self) -> bool:
        ...

    @property
    @abstractmethod
    def provider_type(self) -> EmbeddingProviderType:
        ...
