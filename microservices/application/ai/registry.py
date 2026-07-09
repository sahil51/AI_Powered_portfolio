from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from application.ai.capability import ProviderCapability
from application.ai.exceptions import ProviderConfigurationError, ProviderNotSupportedError
from application.ai.interfaces import AIProvider
from application.ai.models import ModelInfo, ProviderInfo

logger = logging.getLogger("ai_assistant")

ProviderFactoryFn = Callable[[dict[str, Any]], AIProvider]


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._factories: dict[str, ProviderFactoryFn] = {}
        self._default_provider: str | None = None

    def register(self, provider: AIProvider, make_default: bool = False) -> None:
        self._providers[provider.name] = provider
        if make_default or self._default_provider is None:
            self._default_provider = provider.name
        logger.info("Provider registered: %s", provider.name)

    def register_factory(self, name: str, factory: ProviderFactoryFn, make_default: bool = False) -> None:
        self._factories[name] = factory
        if make_default or self._default_provider is None:
            self._default_provider = name
        logger.info("Provider factory registered: %s", name)

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)
        self._factories.pop(name, None)
        if self._default_provider == name:
            if self._providers:
                self._default_provider = next(iter(self._providers))
            elif self._factories:
                self._default_provider = next(iter(self._factories))
            else:
                self._default_provider = None
        logger.info("Provider unregistered: %s", name)

    def get(self, name: str | None = None) -> AIProvider:
        provider_name = name or self._default_provider
        if provider_name is None:
            raise ProviderConfigurationError("No provider registered and no default configured")
        provider = self._providers.get(provider_name)
        if provider is None:
            factory = self._factories.get(provider_name)
            if factory is None:
                raise ProviderConfigurationError(f"Provider '{provider_name}' not found in registry")
            provider = factory({})
            self._providers[provider_name] = provider
        return provider

    def resolve(self, name: str | None = None, capability: ProviderCapability | str | None = None) -> AIProvider:
        provider_name = name or self._default_provider
        if provider_name is None:
            raise ProviderConfigurationError("No provider registered and no default configured")
        provider = self._providers.get(provider_name)
        if provider is not None:
            if capability is None or provider.supports(capability):
                return provider
        for p_name, p in self._providers.items():
            if capability is None or p.supports(capability):
                return p
        for p_name in self._factories:
            if p_name not in self._providers:
                factory = self._factories[p_name]
                provider = factory({})
                self._providers[p_name] = provider
                if capability is None or provider.supports(capability):
                    return provider
        if capability:
            raise ProviderNotSupportedError(f"No provider supports capability: {capability}")
        raise ProviderConfigurationError("No provider available")

    def list_providers(self) -> list[ProviderInfo]:
        result: list[ProviderInfo] = []
        for name, provider in self._providers.items():
            models = provider.list_models()
            result.append(ProviderInfo(name=name, display_name=name, healthy=True, models=models))
        return result

    def list_models(self) -> list[ModelInfo]:
        models: list[ModelInfo] = []
        for provider in self._providers.values():
            try:
                models.extend(provider.list_models())
            except Exception:
                pass
        return models

    @property
    def default(self) -> str | None:
        return self._default_provider

    @default.setter
    def default(self, name: str) -> None:
        if name not in self._providers and name not in self._factories:
            raise ProviderConfigurationError(f"Cannot set default to unknown provider: {name}")
        self._default_provider = name

    @property
    def available(self) -> list[str]:
        return list(self._providers.keys())

    def clear(self) -> None:
        self._providers.clear()
        self._factories.clear()
        self._default_provider = None
        logger.info("Provider registry cleared")


class ProviderFactory:
    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    def create(self, name: str, config: dict[str, Any] | None = None) -> AIProvider:
        factory = self._registry._factories.get(name)
        if factory is None:
            raise ProviderConfigurationError(f"No factory registered for provider: {name}")
        provider = factory(config or {})
        self._registry._providers[name] = provider
        logger.info("Provider created via factory: %s", name)
        return provider
