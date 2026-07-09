from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AgentEvent:
    agent_id: str = ""
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCreated(AgentEvent):
    agent_type: str = ""
    name: str = ""


@dataclass
class AgentInitialized(AgentEvent):
    session_id: str = ""


@dataclass
class AgentStarted(AgentEvent):
    session_id: str = ""


@dataclass
class AgentPaused(AgentEvent):
    reason: str = ""


@dataclass
class AgentResumed(AgentEvent):
    reason: str = ""


@dataclass
class AgentCompleted(AgentEvent):
    result: str = ""


@dataclass
class AgentCancelled(AgentEvent):
    reason: str = ""


@dataclass
class AgentFailed(AgentEvent):
    error: str = ""
    recoverable: bool = False


@dataclass
class AgentArchived(AgentEvent):
    reason: str = ""


@dataclass
class AgentRestarted(AgentEvent):
    session_id: str = ""


@dataclass
class AgentHeartbeat(AgentEvent):
    session_id: str = ""
