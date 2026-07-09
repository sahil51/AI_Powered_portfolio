from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class WorkflowOperation(str, Enum):
    SCHEDULE_MEETING = "schedule_meeting"
    RESCHEDULE_MEETING = "reschedule_meeting"
    CANCEL_MEETING = "cancel_meeting"
    SEND_EMAIL = "send_email"
    CREATE_CRM_LEAD = "create_crm_lead"
    CREATE_REMINDER = "create_reminder"
    NOTIFY_USER = "notify_user"
    CUSTOM = "custom"


class WorkflowResponseStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    RETRY = "retry"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT = "timeout"
    UNEXPECTED_RESPONSE = "unexpected_response"


@dataclass
class WorkflowConfiguration:
    base_url: str = ""
    api_key: str = ""
    api_secret: str = ""
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    retry_backoff_multiplier: float = 2.0
    enable_hmac_signature: bool = False
    hmac_secret: str = ""
    enable_idempotency: bool = True
    headers: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRequest:
    operation: WorkflowOperation = WorkflowOperation.CUSTOM
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    idempotency_key: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowMetadata:
    latency_ms: float = 0.0
    retry_count: int = 0
    status_code: int = 0
    headers: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResponse:
    status: WorkflowResponseStatus = WorkflowResponseStatus.UNEXPECTED_RESPONSE
    success: bool = False
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    http_status: int = 0
    retry_allowed: bool = False
    correlation_id: str = ""
    metadata: WorkflowMetadata = field(default_factory=WorkflowMetadata)


@dataclass
class WorkflowResult:
    success: bool = False
    response: WorkflowResponse | None = None
    error: str | None = None
    latency_ms: float = 0.0
    retry_attempt: int = 0
    correlation_id: str = ""
