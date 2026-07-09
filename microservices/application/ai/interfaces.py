from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from application.ai.capability import ProviderCapability
from application.ai.models import CompletionRequest, CompletionResponse, ModelInfo, ProviderInfo, StreamChunk, Usage


class CompletionInterface(ABC):
    @abstractmethod
    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        ...

    @abstractmethod
    async def generate_json(self, request: CompletionRequest) -> dict:
        ...


class StreamingInterface(ABC):
    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]:
        ...
        yield


class HealthInterface(ABC):
    @abstractmethod
    async def health_check(self) -> bool:
        ...


class TokenCountingInterface(ABC):
    @abstractmethod
    async def count_tokens(self, text: str, model: str | None = None) -> int:
        ...

    @abstractmethod
    async def estimate_tokens(self, text: str) -> int:
        ...


class EmbeddingsInterface(ABC):
    @abstractmethod
    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        ...


class AIProvider(CompletionInterface, StreamingInterface, HealthInterface, TokenCountingInterface, ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def list_models(self) -> list[ModelInfo]:
        ...

    @abstractmethod
    def get_default_model(self) -> str:
        ...

    @abstractmethod
    def get_model(self, model_id: str) -> ModelInfo | None:
        ...

    @abstractmethod
    def supports(self, capability: ProviderCapability | str) -> bool:
        ...

    @abstractmethod
    async def estimate_cost(self, model: str, usage: Usage) -> float:
        ...

    @abstractmethod
    async def get_provider_info(self) -> ProviderInfo:
        ...

    @abstractmethod
    async def initialize(self) -> None:
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        ...
