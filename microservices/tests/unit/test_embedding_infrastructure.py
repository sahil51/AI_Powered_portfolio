from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from application.embedding.models import (
    EmbeddingConfiguration,
    EmbeddingProviderType,
    EmbeddingRequest,
)
from infrastructure.embedding.circuit_breaker import EmbeddingCircuitBreaker
from infrastructure.embedding.config import EmbeddingClientConfig
from infrastructure.embedding.factory import ProviderFactory
from infrastructure.embedding.health import EmbeddingInfraHealth
from infrastructure.embedding.metrics import EmbeddingInfraMetrics
from infrastructure.embedding.providers.gemini import GeminiEmbeddingProvider
from infrastructure.embedding.registry import ProviderRegistry
from infrastructure.embedding.retry import EmbeddingRetryPolicy
from infrastructure.embedding.validator import EmbeddingInfraValidator


class TestEmbeddingClientConfig:
    def test_default_values(self):
        config = EmbeddingClientConfig()
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.circuit_breaker_threshold == 5
        assert config.circuit_breaker_reset_seconds == 60

    def test_from_settings_without_keys(self):
        config = EmbeddingClientConfig.from_settings()
        assert isinstance(config.api_keys, dict)


class TestProviderRegistry:
    def test_register_and_get(self):
        registry = ProviderRegistry()
        provider = MagicMock()
        registry.register(EmbeddingProviderType.GEMINI, provider)
        assert registry.get(EmbeddingProviderType.GEMINI) is provider
        assert registry.get(EmbeddingProviderType.NVIDIA) is None

    def test_list_providers(self):
        registry = ProviderRegistry()
        provider = MagicMock()
        registry.register(EmbeddingProviderType.GEMINI, provider)
        providers = registry.list_providers()
        assert EmbeddingProviderType.GEMINI in providers

    def test_count(self):
        registry = ProviderRegistry()
        assert registry.count == 0
        registry.register(EmbeddingProviderType.GEMINI, MagicMock())
        assert registry.count == 1

    def test_health_of_all(self):
        registry = ProviderRegistry()
        healthy = MagicMock()
        healthy.health_check.return_value = True
        registry.register(EmbeddingProviderType.GEMINI, healthy)
        health = registry.health_of_all()
        assert EmbeddingProviderType.GEMINI in health


class TestEmbeddingRetryPolicy:
    def test_retryable_exceptions(self):
        from application.embedding.exceptions import EmbeddingConnectionError, EmbeddingTimeoutError
        policy = EmbeddingRetryPolicy()
        assert policy.is_retryable(EmbeddingConnectionError("test"))
        assert policy.is_retryable(EmbeddingTimeoutError("test"))
        assert not policy.is_retryable(ValueError("test"))

    def test_delay_increases_with_attempts(self):
        policy = EmbeddingRetryPolicy(base_delay=1.0)
        delay1 = policy.get_delay(0)
        delay2 = policy.get_delay(1)
        delay3 = policy.get_delay(2)
        assert delay1 < delay2 < delay3

    def test_max_delay_capped(self):
        policy = EmbeddingRetryPolicy(base_delay=10.0, max_delay=30.0)
        delay = policy.get_delay(5)
        assert delay <= 30.0


class TestEmbeddingCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = EmbeddingCircuitBreaker(threshold=3, reset_seconds=60)
        assert not cb.is_open("test-provider")

    def test_opens_after_threshold(self):
        cb = EmbeddingCircuitBreaker(threshold=3, reset_seconds=60)
        cb.record_failure("test-provider")
        cb.record_failure("test-provider")
        cb.record_failure("test-provider")
        assert cb.is_open("test-provider")

    def test_closes_below_threshold(self):
        cb = EmbeddingCircuitBreaker(threshold=3, reset_seconds=60)
        cb.record_failure("test-provider")
        cb.record_failure("test-provider")
        assert not cb.is_open("test-provider")

    def test_records_success_resets(self):
        cb = EmbeddingCircuitBreaker(threshold=3, reset_seconds=60)
        cb.record_failure("test-provider")
        cb.record_failure("test-provider")
        cb.record_success("test-provider")
        assert not cb.is_open("test-provider")


class TestEmbeddingInfraHealth:
    @pytest.mark.asyncio
    async def test_check_healthy_provider(self):
        health = EmbeddingInfraHealth("test")
        provider = MagicMock()
        provider.health_check.return_value = True
        result = await health.check(provider)
        assert result.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_check_unhealthy_provider(self):
        health = EmbeddingInfraHealth("test")
        provider = MagicMock()
        provider.health_check.return_value = False
        result = await health.check(provider)
        assert result.status.value != "healthy"


class TestEmbeddingInfraMetrics:
    def test_record_request(self):
        metrics = EmbeddingInfraMetrics()
        metrics.record_request(EmbeddingProviderType.GEMINI, "test-model", 100.0, 50, True)
        assert metrics.metrics.total_requests == 1
        assert metrics.metrics.successful == 1

    def test_record_chunk(self):
        metrics = EmbeddingInfraMetrics()
        metrics.record_chunk()
        assert metrics.metrics.total_chunks_processed == 1

    def test_record_document(self):
        metrics = EmbeddingInfraMetrics()
        metrics.record_document()
        assert metrics.metrics.total_documents_processed == 1

    def test_reset(self):
        metrics = EmbeddingInfraMetrics()
        metrics.record_request(EmbeddingProviderType.GEMINI, "test-model", 100.0)
        metrics.reset()
        assert metrics.metrics.total_requests == 0


class TestEmbeddingInfraValidator:
    def test_validate_configuration_missing_key(self):
        config = EmbeddingClientConfig(api_keys={})
        validator = EmbeddingInfraValidator(config)
        from application.embedding.exceptions import EmbeddingConfigurationError
        config = EmbeddingConfiguration(provider=EmbeddingProviderType.GEMINI, model="test-model")
        validator._client_config.api_keys.pop("gemini", None)
        with pytest.raises(EmbeddingConfigurationError):
            validator.validate_configuration(config)


class TestProviderFactory:
    def test_create_gemini_provider(self):
        config = EmbeddingConfiguration(provider=EmbeddingProviderType.GEMINI, model="text-embedding-004")
        client_config = EmbeddingClientConfig(api_keys={"gemini": "test-key"})
        provider = ProviderFactory.create(EmbeddingProviderType.GEMINI, config, client_config)
        assert isinstance(provider, GeminiEmbeddingProvider)

    def test_create_unsupported_provider(self):
        from application.embedding.exceptions import EmbeddingConfigurationError
        with pytest.raises(EmbeddingConfigurationError):
            ProviderFactory.create(EmbeddingProviderType.CUSTOM)


class TestGeminiEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_provider_type(self):
        config = EmbeddingConfiguration(provider=EmbeddingProviderType.GEMINI, model="text-embedding-004")
        client_config = EmbeddingClientConfig(api_keys={"gemini": "test-key"})
        provider = GeminiEmbeddingProvider(config, client_config)
        assert provider.provider_type == EmbeddingProviderType.GEMINI

    @pytest.mark.asyncio
    async def test_health_check_fails_without_key(self):
        config = EmbeddingConfiguration(provider=EmbeddingProviderType.GEMINI, model="text-embedding-004")
        client_config = EmbeddingClientConfig(api_keys={})
        provider = GeminiEmbeddingProvider(config, client_config)
        healthy = await provider.health_check()
        assert healthy is False

    @pytest.mark.asyncio
    async def test_generate_fails_with_circuit_breaker_open(self):
        config = EmbeddingConfiguration(provider=EmbeddingProviderType.GEMINI, model="text-embedding-004")
        client_config = EmbeddingClientConfig(api_keys={"gemini": "test-key"})
        provider = GeminiEmbeddingProvider(config, client_config)
        provider._circuit_breaker = EmbeddingCircuitBreaker(threshold=1, reset_seconds=60)
        provider._circuit_breaker.record_failure("gemini")

        from application.embedding.exceptions import EmbeddingProviderError
        with pytest.raises(EmbeddingProviderError):
            await provider.generate(EmbeddingRequest(chunk_id="test-chunk", text="test", model="text-embedding-004"))

    @pytest.mark.asyncio
    async def test_close(self):
        config = EmbeddingConfiguration(provider=EmbeddingProviderType.GEMINI, model="text-embedding-004")
        client_config = EmbeddingClientConfig(api_keys={"gemini": "test-key"})
        provider = GeminiEmbeddingProvider(config, client_config)
        await provider.close()
        assert provider._client is None
