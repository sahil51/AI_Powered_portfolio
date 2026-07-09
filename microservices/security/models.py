from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RateLimitScope(str, Enum):
    ANONYMOUS = "anonymous"
    AUTHENTICATED = "authenticated"
    USER = "user"
    TENANT = "tenant"
    WORKFLOW = "workflow"


class AuditAction(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    WORKFLOW_EXECUTION = "workflow_execution"
    KNOWLEDGE_CHANGE = "knowledge_change"
    MEETING_REQUEST = "meeting_request"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"


@dataclass
class AuditEntry:
    action: str
    actor_id: str = ""
    resource_type: str = ""
    resource_id: str = ""
    outcome: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""


@dataclass
class SecretEntry:
    key: str
    value: str
    rotated_at: float = 0.0
    version: int = 1
