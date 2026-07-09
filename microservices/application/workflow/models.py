from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class WorkflowDefinition:
    workflow_id: str = ""
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    timeout: float = 300.0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class WorkflowContext:
    workflow_id: str = ""
    execution_id: str = ""
    correlation_id: str = ""
    trace_id: str = ""
    user_id: str = ""
    conversation_id: str = ""
    session_id: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    checkpoint: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRequest:
    workflow_id: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    trace_id: str = ""
    user_id: str = ""
    conversation_id: str = ""
    session_id: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    timeout: float | None = None
    priority: int = 0


@dataclass
class WorkflowResponse:
    success: bool = True
    output_data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_id: str = ""
    status: WorkflowStatus = WorkflowStatus.COMPLETED
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    execution_id: str = ""
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    checkpoint: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime | None = None
    correlation_id: str = ""
    trace_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    success: bool = True
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_id: str = ""
    status: WorkflowStatus = WorkflowStatus.COMPLETED
    latency_ms: float = 0.0
    steps_completed: int = 0
    total_steps: int = 0
    checkpoint: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowMetadata:
    workflow_id: str = ""
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    timeout: float = 300.0
    max_retries: int = 3
    health: bool = True
    custom: dict[str, Any] = field(default_factory=dict)
