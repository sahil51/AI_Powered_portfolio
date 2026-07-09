import asyncio
import os
from typing import Optional

from litellm import acompletion
from litellm.exceptions import APIConnectionError, InternalServerError, RateLimitError

from config.settings import settings
from exceptions.base import LLMError
from monitoring.logger import logger


class LiteLLMClient:
    def __init__(self):
        self._set_api_keys()

        self.fallback_chain = [
            settings.llm_primary_model,
            f"cerebras/{settings.cerebras_model}",
            f"nvidia/{settings.nvidia_model}",
            f"huggingface/{settings.hf_model}",
        ]
        self.circuit_breaker_state: dict[str, dict] = {}
        self.max_retries = settings.max_tool_retries
        self.circuit_breaker_threshold = settings.circuit_breaker_threshold
        self.circuit_breaker_reset = settings.circuit_breaker_reset_seconds

    def _set_api_keys(self):
        os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key)
        os.environ.setdefault("CEREBRAS_API_KEY", settings.cerebras_api_key)
        os.environ.setdefault("NVIDIA_API_KEY", settings.nvidia_api_key)
        os.environ.setdefault("HUGGINGFACE_API_KEY", settings.hf_token)

    def _is_circuit_open(self, model: str) -> bool:
        state = self.circuit_breaker_state.get(model)
        if not state:
            return False
        if state["failures"] >= self.circuit_breaker_threshold:
            if asyncio.get_event_loop().time() - state["last_failure"] > self.circuit_breaker_reset:
                state["failures"] = 0
                return False
            return True
        return False

    def _record_failure(self, model: str):
        state = self.circuit_breaker_state.setdefault(model, {"failures": 0, "last_failure": 0})
        state["failures"] += 1
        state["last_failure"] = asyncio.get_event_loop().time()

    def _record_success(self, model: str):
        state = self.circuit_breaker_state.get(model)
        if state:
            state["failures"] = 0

    async def acompletion(self, messages: list[dict], tools: Optional[list] = None, **kwargs):
        for model in self.fallback_chain:
            if self._is_circuit_open(model):
                logger.warning(f"Circuit breaker open for {model}, skipping")
                continue
            for attempt in range(self.max_retries):
                try:
                    response = await acompletion(
                        model=model,
                        messages=messages,
                        tools=tools,
                        temperature=kwargs.get("temperature", 0.7),
                        max_tokens=kwargs.get("max_tokens", 2048),
                        timeout=kwargs.get("timeout", 30),
                    )
                    self._record_success(model)
                    return response
                except (APIConnectionError, RateLimitError, InternalServerError) as e:
                    self._record_failure(model)
                    logger.warning(f"Model {model} failed (attempt {attempt + 1}): {e}")
                    if attempt < self.max_retries - 1:
                        wait = 2 ** attempt
                        await asyncio.sleep(wait)
                except Exception as e:
                    logger.error(f"Unexpected error with model {model}: {e}")
                    break
        raise LLMError("All LLM models exhausted or circuit-broken")

    async def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = await self.acompletion(messages, **kwargs)
        return response.choices[0].message.content or ""

    async def generate_with_tools(self, messages: list[dict], tools: list, **kwargs):
        return await self.acompletion(messages, tools=tools, **kwargs)
