from __future__ import annotations

import asyncio
import logging
from typing import Any

from application.ai.exceptions import ProviderTimeoutError

logger = logging.getLogger("ai_assistant")


class LiteLLMMiddleware:
    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    async def apply_timeout(self, coroutine: Any) -> Any:
        try:
            return await asyncio.wait_for(coroutine, timeout=self._timeout)
        except asyncio.TimeoutError:
            raise ProviderTimeoutError(f"Provider timed out after {self._timeout}s")

    def log_request(self, model: str, messages: list[dict]) -> None:
        logger.debug("LLM request to model=%s messages=%d", model, len(messages))

    def log_response(self, model: str, elapsed_ms: float, success: bool) -> None:
        level = logging.DEBUG if success else logging.WARNING
        logger.log(level, "LLM response from model=%s elapsed=%.0fms success=%s", model, elapsed_ms, success)
