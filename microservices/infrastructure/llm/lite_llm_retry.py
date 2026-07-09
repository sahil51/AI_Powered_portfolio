from __future__ import annotations

import asyncio
import logging
from typing import Any

from litellm.exceptions import APIConnectionError, InternalServerError, RateLimitError

from config.settings import settings

logger = logging.getLogger("ai_assistant")

RETRYABLE_EXCEPTIONS = (APIConnectionError, RateLimitError, InternalServerError, TimeoutError)


class LiteLLMRetryPolicy:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ) -> None:
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay

    @property
    def max_retries(self) -> int:
        return self._max_retries

    def is_retryable(self, exception: Exception) -> bool:
        return isinstance(exception, RETRYABLE_EXCEPTIONS)

    def get_delay(self, attempt: int) -> float:
        delay = self._base_delay * (2 ** attempt)
        import random
        jitter = random.uniform(0, 0.1 * delay)
        return min(delay + jitter, self._max_delay)

    async def execute_with_retry(
        self,
        coro_factory: Any,
        on_retry: Any = None,
    ) -> Any:
        last_exception: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return await coro_factory()
            except RETRYABLE_EXCEPTIONS as e:
                last_exception = e
                if on_retry:
                    on_retry(attempt, e)
                if attempt < self._max_retries - 1:
                    delay = self.get_delay(attempt)
                    logger.warning("Retry %d/%d after %s: %s", attempt + 1, self._max_retries, e, delay)
                    await asyncio.sleep(delay)
            except Exception:
                raise
        if last_exception:
            raise last_exception

    @classmethod
    def from_settings(cls) -> LiteLLMRetryPolicy:
        return cls(
            max_retries=settings.max_tool_retries if hasattr(settings, "max_tool_retries") else 3,
        )
