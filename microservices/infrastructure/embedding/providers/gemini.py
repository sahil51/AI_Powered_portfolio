from __future__ import annotations

import time
from typing import Any

import httpx

from application.embedding.exceptions import EmbeddingConnectionError, EmbeddingProviderError, EmbeddingTimeoutError
from application.embedding.models import (
    EmbeddingConfiguration,
    EmbeddingProviderType,
    EmbeddingRequest,
    EmbeddingResponse,
)
from application.embedding.provider import BaseEmbeddingProvider
from infrastructure.embedding.circuit_breaker import EmbeddingCircuitBreaker
from infrastructure.embedding.config import EmbeddingClientConfig
from infrastructure.embedding.health import EmbeddingInfraHealth
from infrastructure.embedding.metrics import EmbeddingInfraMetrics
from infrastructure.embedding.retry import EmbeddingRetryPolicy
from infrastructure.embedding.validator import EmbeddingInfraValidator


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, config: EmbeddingConfiguration, client_config: EmbeddingClientConfig) -> None:
        super().__init__(config)
        self._client_config = client_config
        self._base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self._retry = EmbeddingRetryPolicy(config.max_retries)
        self._circuit_breaker = EmbeddingCircuitBreaker(
            client_config.circuit_breaker_threshold,
            client_config.circuit_breaker_reset_seconds,
        )
        self._infra_health = EmbeddingInfraHealth("gemini")
        self._infra_metrics = EmbeddingInfraMetrics()
        self._infra_validator = EmbeddingInfraValidator(client_config)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._client_config.timeout)
        return self._client

    @property
    def provider_type(self) -> EmbeddingProviderType:
        return EmbeddingProviderType.GEMINI

    async def generate(self, request: EmbeddingRequest) -> EmbeddingResponse:
        if not request.model:
            request.model = self._config.model or "text-embedding-004"
        self._infra_validator.validate_request(request)
        api_key = self._client_config.api_keys.get("gemini", "")

        if self._circuit_breaker.is_open("gemini"):
            raise EmbeddingProviderError("Gemini provider circuit breaker is open")

        try:
            start = time.time()
            response = await self._retry.execute_with_retry(
                lambda: self._call_gemini_api(request, api_key),
            )
            latency_ms = (time.time() - start) * 1000

            embedding_data = response.get("embedding", {})
            values = embedding_data.get("values", [])

            result = EmbeddingResponse(
                chunk_id=request.chunk_id,
                embedding=values,
                dimension=len(values),
                model=request.model or "text-embedding-004",
                tokens_used=response.get("usageMetadata", {}).get("totalTokenCount", 0),
                latency_ms=latency_ms,
            )

            self._validate_embedding_response(request, result)
            self._circuit_breaker.record_success("gemini")
            self._infra_metrics.record_request(
                provider=EmbeddingProviderType.GEMINI,
                model=result.model,
                latency_ms=latency_ms,
                tokens_used=result.tokens_used,
                success=True,
            )
            return result

        except EmbeddingProviderError:
            raise
        except httpx.TimeoutException as e:
            self._circuit_breaker.record_failure("gemini")
            self._infra_metrics.record_request(
                provider=EmbeddingProviderType.GEMINI,
                model=request.model,
                latency_ms=0.0,
                success=False,
            )
            raise EmbeddingTimeoutError(f"Gemini API timeout: {e}")
        except httpx.HTTPStatusError as e:
            self._circuit_breaker.record_failure("gemini")
            self._infra_metrics.record_request(
                provider=EmbeddingProviderType.GEMINI,
                model=request.model,
                latency_ms=0.0,
                success=False,
            )
            raise EmbeddingProviderError(f"Gemini API error: {e.response.status_code} {e.response.text}")
        except Exception as e:
            self._circuit_breaker.record_failure("gemini")
            self._infra_metrics.record_request(
                provider=EmbeddingProviderType.GEMINI,
                model=request.model,
                latency_ms=0.0,
                success=False,
            )
            raise EmbeddingConnectionError(f"Gemini API connection error: {e}")

    async def generate_batch(self, requests: list[EmbeddingRequest]) -> list[EmbeddingResponse]:
        results: list[EmbeddingResponse] = []
        for req in requests:
            results.append(await self.generate(req))
        return results

    async def health_check(self) -> bool:
        try:
            api_key = self._client_config.api_keys.get("gemini", "")
            if not api_key:
                return False
            test_request = EmbeddingRequest(text="health", model=self._config.model or "text-embedding-004")
            await self._call_gemini_api(test_request, api_key)
            return True
        except Exception:
            return False

    async def _call_gemini_api(self, request: EmbeddingRequest, api_key: str) -> dict[str, Any]:
        client = await self._get_client()
        model = request.model or self._config.model or "text-embedding-004"
        url = f"{self._base_url}/{model}:embedContent?key={api_key}"
        payload = {
            "content": {"parts": [{"text": request.text}]},
        }
        response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
