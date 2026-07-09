from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from domain.enums.intent import IntentType


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class ExtractedEntity:
    person_name: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    date: str | None = None
    time: str | None = None
    timezone: str | None = None
    duration: int | None = None
    meeting_type: str | None = None
    priority: str | None = None
    tags: list[str] = field(default_factory=list)
    workflow_parameters: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentContext:
    user_id: str
    session_id: str
    conversation_id: str
    message: str
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    user_type: str = "visitor"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentMetadata:
    latency_ms: float = 0.0
    model: str = ""
    provider: str = ""
    prompt_version: str = ""
    correlation_id: str | None = None
    trace_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentRequest:
    context: IntentContext
    prompt_version: str | None = None
    temperature: float | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    confidence_level: ConfidenceLevel
    entities: ExtractedEntity = field(default_factory=ExtractedEntity)
    needs_confirmation: bool = False
    needs_clarification: bool = False
    missing_fields: list[str] = field(default_factory=list)
    suggested_agent: str | None = None
    workflow_hint: str | None = None
    metadata: IntentMetadata = field(default_factory=IntentMetadata)
    raw_response: str = ""
