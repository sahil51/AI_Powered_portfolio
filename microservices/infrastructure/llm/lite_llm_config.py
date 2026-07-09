from __future__ import annotations

from dataclasses import dataclass, field

from config.settings import settings


@dataclass
class LiteLLMConfiguration:
    primary_model: str = ""
    fallback_models: list[str] = field(default_factory=list)
    api_keys: dict[str, str] = field(default_factory=dict)
    base_urls: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_seconds: int = 60
    max_tokens: int = 2048
    temperature: float = 0.7

    @classmethod
    def from_settings(cls) -> LiteLLMConfiguration:
        primary = settings.llm_primary_model
        fallbacks: list[str] = []
        if settings.cerebras_api_key:
            fallbacks.append(f"cerebras/{settings.cerebras_model}")
        if settings.gemini_api_key:
            fallbacks.append(f"gemini/{settings.gemini_model}")
        if settings.nvidia_api_key:
            fallbacks.append(f"nvidia/{settings.nvidia_model}")
        if settings.hf_token:
            fallbacks.append(f"huggingface/{settings.hf_model}")

        api_keys: dict[str, str] = {}
        if settings.gemini_api_key:
            api_keys["gemini"] = settings.gemini_api_key
        if settings.cerebras_api_key:
            api_keys["cerebras"] = settings.cerebras_api_key
        if settings.nvidia_api_key:
            api_keys["nvidia"] = settings.nvidia_api_key
        if settings.hf_token:
            api_keys["huggingface"] = settings.hf_token

        base_urls: dict[str, str] = {}
        if settings.cerebras_chat_url:
            base_urls["cerebras"] = settings.cerebras_chat_url
        if settings.nvidia_chat_url:
            base_urls["nvidia"] = settings.nvidia_chat_url
        if settings.hf_chat_url:
            base_urls["huggingface"] = settings.hf_chat_url

        max_retries = getattr(settings, "max_tool_retries", 3)
        cb_threshold = getattr(settings, "circuit_breaker_threshold", 5)
        cb_reset = getattr(settings, "circuit_breaker_reset_seconds", 60)

        return cls(
            primary_model=primary,
            fallback_models=fallbacks,
            api_keys=api_keys,
            base_urls=base_urls,
            timeout=max_retries * 10,
            max_retries=max_retries,
            circuit_breaker_threshold=cb_threshold,
            circuit_breaker_reset_seconds=cb_reset,
        )

    def get_api_key(self, provider: str) -> str:
        return self.api_keys.get(provider, "")

    def get_base_url(self, provider: str) -> str:
        return self.base_urls.get(provider, "")
