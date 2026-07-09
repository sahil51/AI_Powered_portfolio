from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.meeting.value_objects import MeetingStatus


@dataclass
class MeetingContext:
    user_id: str = ""
    session_id: str = ""
    conversation_id: str = ""
    correlation_id: str = ""
    message: str = ""
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    intent: str = ""
    intent_confidence: float = 0.0
    confirmation_type: str = ""
    entities: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MeetingSession:
    session_id: str = ""
    meeting_id: str = ""
    user_id: str = ""
    status: MeetingStatus = MeetingStatus.CREATED
    created_at: datetime | None = None
    updated_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    checkpoint: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class MeetingMetadata:
    latency_ms: float = 0.0
    model: str = ""
    provider: str = ""
    correlation_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class MeetingResult:
    meeting_id: str = ""
    status: MeetingStatus = MeetingStatus.CREATED
    title: str = ""
    collected_fields: dict[str, str] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    next_field: str | None = None
    ready_for_workflow: bool = False
    needs_confirmation: bool = False
    needs_clarification: bool = False
    workflow_request: dict[str, Any] | None = None
    message: str = ""
    error: str | None = None
    metadata: MeetingMetadata = field(default_factory=MeetingMetadata)
