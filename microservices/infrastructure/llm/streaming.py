from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from application.ai.models import StreamChunk, Usage

logger = logging.getLogger("ai_assistant")


class LiteLLMStreamHandler:
    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    async def handle_stream(
        self,
        response: Any,
        timeout: float = 30.0,
    ) -> AsyncIterator[StreamChunk]:
        self._cancelled = False
        start = asyncio.get_event_loop().time()
        try:
            async for chunk in response:
                if self._cancelled:
                    break
                if (asyncio.get_event_loop().time() - start) > timeout:
                    logger.warning("Stream timeout after %s seconds", timeout)
                    break
                processed = self._process_chunk(chunk)
                if processed is not None:
                    yield processed
        except Exception as e:
            logger.error("Stream error: %s", e)
        finally:
            await self._cleanup(response)

    def _process_chunk(self, chunk: Any) -> StreamChunk | None:
        try:
            delta = chunk.choices[0].delta if hasattr(chunk, "choices") and chunk.choices else None
            if delta is None:
                return None
            content = getattr(delta, "content", None) or ""
            finish_reason = getattr(chunk.choices[0], "finish_reason", None) if chunk.choices else None
            usage = None
            if hasattr(chunk, "usage") and chunk.usage:
                usage = Usage(
                    prompt_tokens=getattr(chunk.usage, "prompt_tokens", 0) or 0,
                    completion_tokens=getattr(chunk.usage, "completion_tokens", 0) or 0,
                    total_tokens=getattr(chunk.usage, "total_tokens", 0) or 0,
                )
            model = getattr(chunk, "model", "") or ""
            return StreamChunk(
                content=content,
                finish_reason=finish_reason,
                model=model,
                usage=usage,
            )
        except (AttributeError, IndexError, TypeError):
            return None

    async def _cleanup(self, response: Any) -> None:
        try:
            if hasattr(response, "close"):
                await response.close()
        except Exception:
            pass
