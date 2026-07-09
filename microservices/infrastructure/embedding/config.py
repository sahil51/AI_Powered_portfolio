from __future__ import annotations

from dataclasses import dataclass, field

from config.settings import settings


@dataclass
class EmbeddingClientConfig:
    api_keys: dict[str, str] = field(default_factory=dict)
    base_urls: dict[str, str] = field(default_factory=dict)
    default_model: str = ""
    timeout: float = 30.0
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_seconds: int = 60

    @classmethod
    def from_settings(cls) -> EmbeddingClientConfig:
        api_keys: dict[str, str] = {}
        if settings.gemini_api_key:
            api_keys["gemini"] = settings.gemini_api_key
        if settings.nvidia_api_key:
            api_keys["nvidia"] = settings.nvidia_api_key

        default_model = settings.embedding_model or "text-embedding-004"

        return cls(
            api_keys=api_keys,
            default_model=default_model,
            timeout=30.0,
            max_retries=3,
            circuit_breaker_threshold=5,
            circuit_breaker_reset_seconds=60,
        )
