from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    correlation_id: str = ""
    conversation_id: str = ""
    request_id: str = ""
    workflow_id: str = ""
    trace_id: str = ""
    user_id: str = ""
    tenant_id: str = ""
    agent_id: str = ""
    knowledge_document_id: str = ""


@dataclass
class SpanData:
    span_id: str
    trace_id: str
    parent_span_id: str = ""
    operation_name: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    status: str = "ok"
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MetricsData:
    http_requests_total: int = 0
    http_errors_total: int = 0
    http_latency_ms_total: float = 0.0
    conversation_total: int = 0
    memory_operations_total: int = 0
    knowledge_operations_total: int = 0
    retrieval_operations_total: int = 0
    embedding_operations_total: int = 0
    prompt_operations_total: int = 0
    provider_calls_total: int = 0
    intent_operations_total: int = 0
    confirmation_operations_total: int = 0
    meeting_operations_total: int = 0
    workflow_operations_total: int = 0
    redis_operations_total: int = 0
    postgresql_operations_total: int = 0
    celery_tasks_total: int = 0
    n8n_operations_total: int = 0
    errors_total: int = 0
    retries_total: int = 0
    tokens_used_total: int = 0
    cost_total: float = 0.0
