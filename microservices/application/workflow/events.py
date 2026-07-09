from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class WorkflowEvent:
    event_id: str = ""
    workflow_id: str = ""
    execution_id: str = ""
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStarted(WorkflowEvent):
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowPaused(WorkflowEvent):
    reason: str = ""


@dataclass
class WorkflowResumed(WorkflowEvent):
    reason: str = ""


@dataclass
class WorkflowCompleted(WorkflowEvent):
    output: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowCancelled(WorkflowEvent):
    reason: str = ""


@dataclass
class WorkflowFailed(WorkflowEvent):
    error: str = ""
    recoverable: bool = False


@dataclass
class WorkflowCheckpoint(WorkflowEvent):
    checkpoint_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRecovered(WorkflowEvent):
    recovery_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRetried(WorkflowEvent):
    attempt: int = 0
    max_attempts: int = 3
    error: str = ""
