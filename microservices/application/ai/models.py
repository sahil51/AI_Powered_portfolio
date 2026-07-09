from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cost=self.cost + other.cost,
        )


@dataclass
class CompletionRequest:
    model: str = ""
    system_prompt: str | None = None
    messages: list[dict[str, str]] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: float = 30.0
    top_p: float = 1.0
    stop: list[str] | None = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    seed: int | None = None
    user: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    stream: bool = False
    response_format: dict[str, Any] | None = None

    def to_messages(self) -> list[dict[str, str]]:
        if self.system_prompt:
            return [{"role": "system", "content": self.system_prompt}] + self.messages
        return self.messages


@dataclass
class StreamChunk:
    content: str = ""
    finish_reason: str | None = None
    model: str = ""
    usage: Usage | None = None


@dataclass
class CompletionResponse:
    content: str
    model: str = ""
    usage: Usage = field(default_factory=Usage)
    finish_reason: str = ""
    provider: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelCapabilities:
    max_context_length: int = 0
    max_output_tokens: int = 0
    supports_streaming: bool = False
    supports_json_mode: bool = False
    supports_function_calling: bool = False
    supports_tool_calling: bool = False
    supports_parallel_tool_calling: bool = False
    supports_vision: bool = False
    supports_embeddings: bool = False
    supports_structured_output: bool = False

    def has(self, capability: str) -> bool:
        mapping = {
            "completion": True,
            "streaming": self.supports_streaming,
            "json_mode": self.supports_json_mode,
            "function_calling": self.supports_function_calling,
            "tool_calling": self.supports_tool_calling,
            "parallel_tool_calling": self.supports_parallel_tool_calling,
            "vision": self.supports_vision,
            "embeddings": self.supports_embeddings,
            "structured_output": self.supports_structured_output,
        }
        return mapping.get(capability, False)


@dataclass
class ModelInfo:
    id: str
    provider: str = ""
    display_name: str = ""
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    priority: int = 0
    healthy: bool = True


@dataclass
class ProviderInfo:
    name: str
    display_name: str = ""
    version: str = "1.0.0"
    healthy: bool = True
    models: list[ModelInfo] = field(default_factory=list)
    priority: int = 0
    capabilities: list[str] = field(default_factory=list)
