from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from application.ai.models import Usage


class PipelineStage(str, Enum):
    VALIDATE_INPUT = "validate_input"
    LOAD_CONVERSATION = "load_conversation"
    LOAD_MEMORY = "load_memory"
    BUILD_CONTEXT = "build_context"
    LOAD_PROMPT = "load_prompt"
    RENDER_PROMPT = "render_prompt"
    ESTIMATE_TOKENS = "estimate_tokens"
    VALIDATE_BUDGET = "validate_budget"
    SELECT_PROVIDER = "select_provider"
    GENERATE = "generate"
    VALIDATE_RESPONSE = "validate_response"
    POST_PROCESS = "post_process"
    COLLECT_METRICS = "collect_metrics"


@dataclass
class PipelineConfiguration:
    default_provider: str | None = None
    default_prompt_category: str = "system"
    default_prompt_name: str = "system.system"
    max_retries: int = 3
    fallback_enabled: bool = True
    streaming_enabled: bool = False
    timeout: float = 60.0
    max_output_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 1.0
    enable_tracing: bool = False
    enable_metrics: bool = True
    budget_validation: bool = True
    response_validation: bool = True
    post_processing: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineContext:
    conversation_id: str
    user_id: str
    session_id: str = ""
    prompt_category: str = "system"
    prompt_name: str = "system.system"
    prompt_version: str | None = None
    prompt_variables: dict[str, Any] = field(default_factory=dict)
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    streaming: bool = False
    model_override: str | None = None
    provider_override: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolve_temperature(self, default: float = 0.7) -> float:
        return self.temperature if self.temperature is not None else default

    def resolve_top_p(self, default: float = 1.0) -> float:
        return self.top_p if self.top_p is not None else default

    def resolve_max_tokens(self, default: int = 2048) -> int:
        return self.max_tokens if self.max_tokens is not None else default


@dataclass
class PipelineStageResult:
    stage: PipelineStage
    success: bool
    latency_ms: float = 0.0
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    content: str
    provider: str
    model: str
    latency_ms: float
    token_usage: Usage
    estimated_cost: float
    finish_reason: str
    correlation_id: str | None = None
    trace_id: str | None = None
    warnings: list[str] = field(default_factory=list)
    stage_results: list[PipelineStageResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    streaming: bool = False
