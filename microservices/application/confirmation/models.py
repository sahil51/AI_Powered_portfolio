from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.enums.confirmation import ConfirmationType
from domain.enums.intent import IntentType


@dataclass
class ConfirmationContext:
    user_id: str
    session_id: str
    conversation_id: str
    user_reply: str
    current_intent: IntentType | None = None
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    pending_questions: list[str] = field(default_factory=list)
    pending_fields: list[str] = field(default_factory=list)
    current_entities: dict[str, Any] = field(default_factory=dict)
    workflow_context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfirmationMetadata:
    latency_ms: float = 0.0
    model: str = ""
    provider: str = ""
    prompt_version: str = ""
    correlation_id: str | None = None
    trace_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfirmationResult:
    confirmation_type: ConfirmationType
    confirmed: bool = False
    updated_entities: dict[str, Any] = field(default_factory=dict)
    remaining_missing_fields: list[str] = field(default_factory=list)
    corrected_field: str | None = None
    corrected_value: str | None = None
    reason: str = ""
    suggested_follow_up: str = ""
    ready_for_agent: bool = False
    workflow_hint: str | None = None
    metadata: ConfirmationMetadata = field(default_factory=ConfirmationMetadata)
    raw_response: str = ""
