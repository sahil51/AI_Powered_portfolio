from __future__ import annotations

import asyncio
import os
import time
from collections.abc import AsyncIterator
from typing import Any

from litellm import acompletion
from litellm.exceptions import APIConnectionError, InternalServerError, RateLimitError

from application.ai.capability import ProviderCapability
from application.ai.exceptions import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from application.ai.interfaces import AIProvider
from application.ai.models import (
    CompletionRequest,
    CompletionResponse,
    ModelInfo,
    ProviderInfo,
    StreamChunk,
    Usage,
)
from infrastructure.llm.fallback import FallbackStrategy
from infrastructure.llm.lite_llm_config import LiteLLMConfiguration
from infrastructure.llm.lite_llm_health import LiteLLMHealth
from infrastructure.llm.lite_llm_metrics import LiteLLMMetrics
from infrastructure.llm.lite_llm_middleware import LiteLLMMiddleware
from infrastructure.llm.lite_llm_retry import LiteLLMRetryPolicy
from infrastructure.llm.lite_llm_validator import LiteLLMValidator
from infrastructure.llm.model_registry import ModelDefinition, ModelRegistry
from infrastructure.llm.streaming import LiteLLMStreamHandler
from infrastructure.llm.token_counter import LiteLLMTokenCounter
from monitoring.logger import logger

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class LiteLLMProvider(AIProvider):
    def __init__(self, config: LiteLLMConfiguration | None = None) -> None:
        self._config = config or LiteLLMConfiguration.from_settings()
        self._validator = LiteLLMValidator()
        self._metrics = LiteLLMMetrics()
        self._health = LiteLLMHealth(provider_name="litellm")
        self._middleware = LiteLLMMiddleware(timeout=self._config.timeout)
        self._retry_policy = LiteLLMRetryPolicy(max_retries=self._config.max_retries)
        self._token_counter = LiteLLMTokenCounter()
        self._stream_handler = LiteLLMStreamHandler()
        self._model_registry = ModelRegistry()
        self._circuit_breaker_state: dict[str, dict] = {}
        self._initialized = False

        self._fallback = FallbackStrategy(
            fallback_models=self._config.fallback_models,
            circuit_breaker_state=self._circuit_breaker_state,
            metrics_collector=self._metrics,
            circuit_breaker_threshold=self._config.circuit_breaker_threshold,
            circuit_breaker_reset=self._config.circuit_breaker_reset_seconds,
        )

    @property
    def name(self) -> str:
        return "litellm"

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._set_api_keys()
        self._register_models()
        self._initialized = True
        logger.info("LiteLLMProvider initialized with primary model: %s", self._config.primary_model)

    async def shutdown(self) -> None:
        self._initialized = False
        logger.info("LiteLLMProvider shut down")

    def _set_api_keys(self) -> None:
        for provider_key, env_var in [
            ("gemini", "GEMINI_API_KEY"),
            ("cerebras", "CEREBRAS_API_KEY"),
            ("nvidia", "NVIDIA_API_KEY"),
            ("huggingface", "HF_TOKEN"),
        ]:
            key = self._config.get_api_key(provider_key)
            if key:
                os.environ.setdefault(env_var, key)

    def _register_models(self) -> None:
        models: list[ModelDefinition] = [
            ModelDefinition(
                id=self._config.primary_model,
                provider="gemini",
                display_name="Gemini 2.0 Flash",
                max_context_length=1048576,
                max_output_tokens=8192,
                supports_vision=True,
                priority=0,
            ),
        ]
        for i, fallback_model in enumerate(self._config.fallback_models):
            provider = fallback_model.split("/")[0] if "/" in fallback_model else "unknown"
            models.append(
                ModelDefinition(
                    id=fallback_model,
                    provider=provider,
                    display_name=fallback_model,
                    max_context_length=32768,
                    max_output_tokens=4096,
                    priority=i + 1,
                )
            )
        self._model_registry.register_many(models)

    def _get_provider_from_model(self, model: str) -> str:
        return model.split("/")[0] if "/" in model else "unknown"

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        self._ensure_initialized()
        self._validator.validate_request(request)

        model = request.model or self.get_default_model()
        messages = request.to_messages()

        request.model = model
        self._middleware.log_request(model, messages)

        start = time.time()
        try:
            response = await self._fallback.execute_with_fallback(
                primary_model=model,
                request_fn=lambda m: self._acomplete(m, messages, request),
            )
            elapsed = (time.time() - start) * 1000
            self._middleware.log_response(model, elapsed, True)
            usage = self._extract_usage(response, model)
            self._metrics.record_request("litellm", model, True, elapsed, usage)
            return self._to_completion_response(response, model)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            self._middleware.log_response(model, elapsed, False)
            self._metrics.record_request("litellm", model, False, elapsed)
            raise self._map_error(e, model)

    async def generate_json(self, request: CompletionRequest) -> dict:
        request.response_format = {"type": "json_object"}
        response = await self.generate(request)
        import json

        try:
            return json.loads(response.content)
        except json.JSONDecodeError as e:
            raise ProviderError("Failed to parse JSON response", detail=str(e))

    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]:
        self._ensure_initialized()
        self._validator.validate_request(request)

        model = request.model or self.get_default_model()
        messages = request.to_messages()
        request.stream = True

        self._middleware.log_request(model, messages)

        try:
            response = await acompletion(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                timeout=request.timeout,
                stream=True,
            )
            async for chunk in self._stream_handler.handle_stream(response, timeout=request.timeout):
                yield chunk
        except Exception as e:
            logger.error("Stream error for model %s: %s", model, e)
            raise self._map_error(e, model)

    async def count_tokens(self, text: str, model: str | None = None) -> int:
        return await self._token_counter.count_tokens(text, model)

    async def estimate_tokens(self, text: str) -> int:
        return await self._token_counter.estimate_tokens(text)

    async def health_check(self) -> bool:
        try:
            test_text = "test"
            tokens = await self.count_tokens(test_text)
            return tokens > 0
        except Exception:
            return False

    def list_models(self) -> list[ModelInfo]:
        return self._model_registry.list_models()

    def get_default_model(self) -> str:
        return self._config.primary_model

    def get_model(self, model_id: str) -> ModelInfo | None:
        model_def = self._model_registry.get(model_id)
        if model_def is None:
            return None
        return model_def.to_model_info()

    def supports(self, capability: ProviderCapability | str) -> bool:
        cap_str = capability.value if isinstance(capability, ProviderCapability) else capability
        models = self._model_registry.list_models()
        return any(m.capabilities.has(cap_str) for m in models)

    async def estimate_cost(self, model: str, usage: Usage) -> float:
        return self._token_counter.estimate_cost(model, usage)

    async def get_provider_info(self) -> ProviderInfo:
        models = self.list_models()
        caps: list[str] = []
        for cap in ProviderCapability:
            if self.supports(cap):
                caps.append(cap.value)
        return ProviderInfo(
            name=self.name,
            display_name="LiteLLM Provider",
            version="1.0.0",
            healthy=self._initialized,
            models=models,
            priority=0,
            capabilities=caps,
        )

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise ProviderConfigurationError("LiteLLMProvider not initialized. Call initialize() first.")

    async def _acomplete(self, model: str, messages: list[dict], request: CompletionRequest) -> Any:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "timeout": request.timeout,
            "top_p": request.top_p,
        }
        if request.stop:
            kwargs["stop"] = request.stop
        if request.presence_penalty:
            kwargs["presence_penalty"] = request.presence_penalty
        if request.frequency_penalty:
            kwargs["frequency_penalty"] = request.frequency_penalty
        if request.seed is not None:
            kwargs["seed"] = request.seed
        if request.response_format:
            kwargs["response_format"] = request.response_format
        if request.user:
            kwargs["user"] = request.user

        return await self._middleware.apply_timeout(acompletion(**kwargs))

    def _extract_usage(self, response: Any, model: str) -> Usage:
        usage = Usage()
        if hasattr(response, "usage") and response.usage:
            usage.prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            usage.completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            usage.total_tokens = getattr(response.usage, "total_tokens", 0) or 0
        usage.cost = self._token_counter.estimate_cost(model, usage)
        return usage

    def _to_completion_response(self, response: Any, model: str) -> CompletionResponse:
        content = ""
        finish_reason = ""
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            if hasattr(choice, "message") and choice.message:
                content = getattr(choice.message, "content", None) or ""
            finish_reason = getattr(choice, "finish_reason", None) or ""
        usage = self._extract_usage(response, model)
        return CompletionResponse(
            content=content,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
            provider=self.name,
            raw={},
        )

    def _map_error(self, error: Exception, model: str) -> Exception:
        if isinstance(error, ProviderError):
            return error
        if isinstance(error, asyncio.TimeoutError):
            return ProviderTimeoutError(
                message=f"Provider timeout for model {model}",
                provider=self.name,
            )
        if isinstance(error, RateLimitError):
            return ProviderRateLimitError(
                message=f"Rate limit exceeded for model {model}",
                provider=self.name,
            )
        if "authentication" in str(error).lower() or "api key" in str(error).lower():
            return ProviderAuthenticationError(
                message=f"Authentication failed for model {model}",
                provider=self.name,
            )
        if isinstance(error, (APIConnectionError, InternalServerError)):
            return ProviderUnavailableError(
                message=f"Provider unavailable for model {model}: {error}",
                provider=self.name,
            )
        return ProviderError(
            message=f"Provider error for model {model}: {error}",
            provider=self.name,
        )
