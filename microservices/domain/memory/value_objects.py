import uuid
from dataclasses import dataclass, field
from enum import Enum


class MemoryScope(str, Enum):
    GLOBAL = "global"
    USER = "user"
    CONVERSATION = "conversation"
    SESSION = "session"
    MEETING = "meeting"
    LEAD = "lead"


class MemoryPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class MemoryConfidence(str, Enum):
    CERTAIN = "certain"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFERRED = "inferred"
    UNCERTAIN = "uncertain"


class MemoryCategory(str, Enum):
    PROFILE = "profile"
    PREFERENCE = "preference"
    SEMANTIC = "semantic"
    CONVERSATION = "conversation"
    MEETING = "meeting"
    LEAD = "lead"
    RELATIONSHIP = "relationship"
    FACT = "fact"


class MemorySource(str, Enum):
    USER_INPUT = "user_input"
    ASSISTANT_INFERENCE = "assistant_inference"
    SYSTEM = "system"
    MEETING_SCHEDULER = "meeting_scheduler"
    LEAD_CAPTURE = "lead_capture"
    EXTERNAL_API = "external_api"
    MANUAL = "manual"
    MIGRATION = "migration"


class MemoryImportance(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


@dataclass(frozen=True)
class MemoryId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class MemoryKey:
    namespace: str
    key: str

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}"
