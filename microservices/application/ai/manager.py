from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from application.ai.capability import ProviderCapability
from application.ai.exceptions import ProviderError, ProviderNotSupportedError
from application.ai.interfaces import AIProvider
from application.ai.models import CompletionRequest, CompletionResponse, StreamChunk
from application.ai.registry import ProviderRegistry

logger = logging.getLogger("ai_assistant")


class ProviderManager:
    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    async def generate(
        self,
        request: CompletionRequest,
        provider_name: str | None = None,
    ) -> CompletionResponse:
        provider = self._resolve(provider_name, ProviderCapability.COMPLETION)
        return await provider.generate(request)

    async def generate_json(
        self,
        request: CompletionRequest,
        provider_name: str | None = None,
    ) -> dict:
        provider = self._resolve(provider_name, ProviderCapability.JSON_MODE)
        return await provider.generate_json(request)

    async def stream(
        self,
        request: CompletionRequest,
        provider_name: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        provider = self._resolve(provider_name, ProviderCapability.STREAMING)
        async for chunk in provider.stream(request):
            yield chunk

    async def count_tokens(
        self,
        text: str,
        model: str | None = None,
        provider_name: str | None = None,
    ) -> int:
        provider = self._resolve(provider_name, ProviderCapability.TOKEN_COUNTING)
        return await provider.count_tokens(text, model)

    async def health_check(self, provider_name: str | None = None) -> bool:
        provider = self._resolve(provider_name, ProviderCapability.HEALTH_CHECK)
        return await provider.health_check()

    async def check_all_health(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for name in self._registry.available:
            try:
                provider = self._registry.get(name)
                results[name] = await provider.health_check()
            except Exception:
                results[name] = False
        return results

    def list_models(self, provider_name: str | None = None) -> list[Any]:
        if provider_name:
            provider = self._registry.get(provider_name)
            return provider.list_models()
        return self._registry.list_models()

    def get_default_model(self, provider_name: str | None = None) -> str:
        provider = self._registry.get(provider_name)
        return provider.get_default_model()

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    def _resolve(self, provider_name: str | None, capability: ProviderCapability | str) -> AIProvider:
        try:
            return self._registry.resolve(provider_name, capability)
        except ProviderNotSupportedError:
            raise ProviderNotSupportedError(
                f"No provider supports capability '{capability}'",
                detail=f"Requested provider: {provider_name}",
            )
        except ProviderError:
            raise

    async def initialize_all(self) -> None:
        for name in self._registry.available:
            try:
                provider = self._registry.get(name)
                await provider.initialize()
                logger.info("Provider initialized: %s", name)
            except Exception as e:
                logger.error("Failed to initialize provider %s: %s", name, e)

    async def shutdown_all(self) -> None:
        for name in self._registry.available:
            try:
                provider = self._registry.get(name)
                await provider.shutdown()
                logger.info("Provider shut down: %s", name)
            except Exception as e:
                logger.error("Error shutting down provider %s: %s", name, e)
