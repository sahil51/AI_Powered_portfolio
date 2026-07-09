import uuid
from dataclasses import dataclass, field
from enum import Enum


class AgentType(str, Enum):
    CONVERSATION = "conversation"
    MEETING = "meeting"
    INTENT = "intent"
    CONFIRMATION = "confirmation"
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"
    MEMORY = "memory"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    ARCHIVED = "archived"


class AgentCapability(str, Enum):
    CONVERSATION = "conversation"
    MEMORY_MANAGEMENT = "memory_management"
    INTENT_CLASSIFICATION = "intent_classification"
    CONFIRMATION = "confirmation"
    WORKFLOW_EXECUTION = "workflow_execution"
    ANALYSIS = "analysis"
    SCHEDULING = "scheduling"
    CUSTOM = "custom"


class AgentPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class AgentHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AgentId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AgentId):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass(frozen=True)
class AgentVersion:
    major: int = 1
    minor: int = 0
    patch: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, version: str) -> "AgentVersion":
        parts = version.split(".")
        major = int(parts[0]) if len(parts) > 0 else 1
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return cls(major=major, minor=minor, patch=patch)


@dataclass(frozen=True)
class AgentMetadata:
    display_name: str = ""
    description: str = ""
    version: AgentVersion = field(default_factory=AgentVersion)
    author: str = ""
    tags: tuple[str, ...] = ()
    custom: dict[str, str] = field(default_factory=dict)
