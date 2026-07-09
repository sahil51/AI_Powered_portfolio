from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from monitoring.logger import logger
from security.circuit_breaker_registry import CircuitBreakerRegistry
from security.retry_policy_registry import RetryPolicyRegistry

T = TypeVar("T")


class TimeoutPolicy:
    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds


class BulkheadPolicy:
    def __init__(self, max_concurrent: int = 10, max_queue: int = 20) -> None:
        self.max_concurrent = max_concurrent
        self.max_queue = max_queue
        self._semaphore: asyncio.Semaphore | None = None

    async def acquire(self) -> None:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        await self._semaphore.acquire()

    def release(self) -> None:
        if self._semaphore:
            self._semaphore.release()


_FT = TypeVar("_FT")


class FallbackPolicy(Generic[_FT]):
    def __init__(
        self,
        fallback_func: Callable[..., Awaitable[_FT]] | None = None,
        default_value: _FT | None = None,
    ) -> None:
        self._fallback_func = fallback_func
        self.default_value = default_value

    async def execute_fallback(self, *args: Any, **kwargs: Any) -> _FT:
        if self._fallback_func:
            return await self._fallback_func(*args, **kwargs)
        if self.default_value is not None:
            return self.default_value
        raise RuntimeError("No fallback available")


_GT = TypeVar("_GT")


class GracefulDegradationPolicy(Generic[_GT]):
    def __init__(self, degraded_func: Callable[..., Awaitable[_GT]] | None = None) -> None:
        self._degraded_func = degraded_func

    async def execute_degraded(self, *args: Any, **kwargs: Any) -> _GT:
        if self._degraded_func:
            logger.warning("Executing degraded function")
            return await self._degraded_func(*args, **kwargs)
        raise RuntimeError("No degraded function available")


class ResilienceManager:
    def __init__(
        self,
        circuit_breaker_registry: CircuitBreakerRegistry,
        retry_policy_registry: RetryPolicyRegistry,
    ) -> None:
        self._circuit_breaker_registry = circuit_breaker_registry
        self._retry_policy_registry = retry_policy_registry
        self._bulkheads: dict[str, BulkheadPolicy] = {}
        self._timeouts: dict[str, TimeoutPolicy] = {}
        self._degradation: dict[str, GracefulDegradationPolicy] = {}
        self._fallbacks: dict[str, FallbackPolicy] = {}

    @property
    def circuit_breaker_registry(self) -> CircuitBreakerRegistry:
        return self._circuit_breaker_registry

    @property
    def retry_policy_registry(self) -> RetryPolicyRegistry:
        return self._retry_policy_registry

    def register_bulkhead(self, name: str, max_concurrent: int = 10, max_queue: int = 20) -> None:
        self._bulkheads[name] = BulkheadPolicy(max_concurrent=max_concurrent, max_queue=max_queue)

    def register_timeout(self, name: str, timeout_seconds: float = 30.0) -> None:
        self._timeouts[name] = TimeoutPolicy(timeout_seconds=timeout_seconds)

    def register_degradation(self, name: str, degraded_func: Callable[..., Awaitable[T]]) -> None:
        self._degradation[name] = GracefulDegradationPolicy(degraded_func=degraded_func)

    def register_fallback(
        self, name: str,
        fallback_func: Callable[..., Awaitable[T]] | None = None,
        default_value: Any = None,
    ) -> None:
        self._fallbacks[name] = FallbackPolicy(fallback_func=fallback_func, default_value=default_value)

    async def execute_with_resilience(
        self,
        name: str,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        if not self._circuit_breaker_registry.is_available(name):
            logger.warning(f"Circuit breaker open for {name}, attempting fallback")
            if name in self._fallbacks:
                return await self._fallbacks[name].execute_fallback(*args, **kwargs)
            if name in self._degradation:
                return await self._degradation[name].execute_degraded(*args, **kwargs)
            raise RuntimeError(f"Circuit breaker open for {name} and no fallback available")

        timeout = self._timeouts.get(name)
        bulkhead = self._bulkheads.get(name)

        async def execute() -> T:
            if bulkhead:
                await bulkhead.acquire()
            try:
                if timeout:
                    result = await asyncio.wait_for(
                        self._execute_with_cb_and_retry(name, func, *args, **kwargs),
                        timeout=timeout.timeout_seconds,
                    )
                else:
                    result = await self._execute_with_cb_and_retry(name, func, *args, **kwargs)
                return result
            except asyncio.TimeoutError:
                self._circuit_breaker_registry.record_failure(name)
                logger.error(f"Timeout executing {name}")
                raise
            finally:
                if bulkhead:
                    bulkhead.release()

        return await execute()

    async def _execute_with_cb_and_retry(
        self,
        name: str,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        try:
            result = await self._retry_policy_registry.execute_with_retry(
                name, name, func, *args, **kwargs,
            )
            self._circuit_breaker_registry.record_success(name)
            return result
        except Exception:
            self._circuit_breaker_registry.record_failure(name)
            raise

    def get_resilience_report(self) -> dict[str, Any]:
        return {
            "circuit_breakers": self._circuit_breaker_registry.get_all_states(),
            "bulkheads": {
                name: {"max_concurrent": b.max_concurrent, "max_queue": b.max_queue}
                for name, b in self._bulkheads.items()
            },
            "timeouts": {name: {"timeout_seconds": t.timeout_seconds} for name, t in self._timeouts.items()},
        }

    def reset(self) -> None:
        self._circuit_breaker_registry.reset_all()
        self._bulkheads.clear()
        self._timeouts.clear()
        self._degradation.clear()
        self._fallbacks.clear()
