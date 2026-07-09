from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from monitoring.logger import logger

T = TypeVar("T")


class BackoffStrategy(Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    JITTER = "jitter"


@dataclass
class RetryPolicy:
    name: str
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)
    jitter_factor: float = 0.1


class RetryPolicyRegistry:
    def __init__(self) -> None:
        self._policies: dict[str, RetryPolicy] = {}

    def register(self, policy: RetryPolicy) -> None:
        self._policies[policy.name] = policy

    def get(self, name: str) -> RetryPolicy | None:
        return self._policies.get(name)

    def get_or_default(self, name: str) -> RetryPolicy:
        policy = self._policies.get(name)
        if policy is None:
            return RetryPolicy(name=name)
        return policy

    def register_defaults(self) -> None:
        self.register(RetryPolicy(
            name="default",
            max_retries=3,
            base_delay_seconds=1.0,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
        ))
        self.register(RetryPolicy(
            name="fast",
            max_retries=2,
            base_delay_seconds=0.5,
            backoff_strategy=BackoffStrategy.FIXED,
        ))
        self.register(RetryPolicy(
            name="persistent",
            max_retries=5,
            base_delay_seconds=2.0,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            max_delay_seconds=120.0,
        ))
        self.register(RetryPolicy(
            name="circuit_breaker_safe",
            max_retries=2,
            base_delay_seconds=5.0,
            backoff_strategy=BackoffStrategy.JITTER,
        ))

    def calculate_delay(self, policy: RetryPolicy, attempt: int) -> float:
        if policy.backoff_strategy == BackoffStrategy.FIXED:
            delay = policy.base_delay_seconds
        elif policy.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = policy.base_delay_seconds * (2 ** attempt)
        elif policy.backoff_strategy == BackoffStrategy.LINEAR:
            delay = policy.base_delay_seconds * (attempt + 1)
        elif policy.backoff_strategy == BackoffStrategy.JITTER:
            delay = policy.base_delay_seconds * (2 ** attempt)
            delay = delay + random.uniform(0, delay * policy.jitter_factor)
        else:
            delay = policy.base_delay_seconds
        return min(delay, policy.max_delay_seconds)

    async def execute_with_retry(
        self,
        policy_name: str,
        operation_name: str,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        policy = self.get_or_default(policy_name)
        last_exception: Exception | None = None

        for attempt in range(policy.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except policy.retryable_exceptions as e:
                last_exception = e
                if attempt < policy.max_retries:
                    delay = self.calculate_delay(policy, attempt)
                    logger.info(
                        f"Retry {attempt + 1}/{policy.max_retries} for {operation_name} "
                        f"after {delay:.2f}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {policy.max_retries + 1} retries exhausted for {operation_name}: {e}"
                    )
                    raise
            except Exception:
                raise

        if last_exception:
            raise last_exception

        raise RuntimeError(f"Unexpected: execute_with_retry completed without result for {operation_name}")
