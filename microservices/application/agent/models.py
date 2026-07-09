from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AgentContext:
    agent_id: str = ""
    session_id: str = ""
    user_id: str = ""
    conversation_id: str = ""
    correlation_id: str = ""
    trace_id: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentSession:
    session_id: str = ""
    agent_id: str = ""
    user_id: str = ""
    status: str = "created"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    checkpoint: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    retry_count: int = 0


@dataclass
class AgentConfiguration:
    timeout: float = 300.0
    max_retries: int = 3
    enable_heartbeat: bool = True
    enable_checkpoint: bool = True
    enable_recovery: bool = True
    heartbeat_interval: float = 30.0
    checkpoint_interval: float = 60.0
    max_concurrent: int = 10
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentStatistics:
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    pause_count: int = 0
    resume_count: int = 0
    cancel_count: int = 0
    retry_count: int = 0
    timeout_count: int = 0
    heartbeat_count: int = 0
    checkpoint_count: int = 0
    recovery_count: int = 0
    last_execution_time: float = 0.0
    state_transitions: dict[str, int] = field(default_factory=dict)
