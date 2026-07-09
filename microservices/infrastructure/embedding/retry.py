from __future__ import annotations

import asyncio
import random
from collections.abc import Callable
from typing import Any

from application.embedding.exceptions import EmbeddingConnectionError, EmbeddingTimeoutError

RETRYABLE = (EmbeddingConnectionError, EmbeddingTimeoutError)


class EmbeddingRetryPolicy:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0) -> None:
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay

    def is_retryable(self, exception: Exception) -> bool:
        return isinstance(exception, RETRYABLE)

    def get_delay(self, attempt: int) -> float:
        delay = self._base_delay * (2 ** attempt)
        jitter = random.uniform(0, 0.1 * delay)
        return min(delay + jitter, self._max_delay)

    async def execute_with_retry(
        self,
        fn: Callable[[], Any],
        on_retry: Callable[[Exception, int], None] | None = None,
    ) -> Any:
        last_exception: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                result = fn()
                if asyncio.iscoroutine(result):
                    return await result
                return result
            except RETRYABLE as e:
                last_exception = e
                if on_retry:
                    on_retry(e, attempt)
                if attempt < self._max_retries:
                    await asyncio.sleep(self.get_delay(attempt))
                else:
                    raise
        if last_exception:
            raise last_exception
