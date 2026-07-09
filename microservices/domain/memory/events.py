from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class MemoryEvent:
    event_id: str = ""
    memory_id: str = ""
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryCreated(MemoryEvent):
    user_id: str = ""
    category: str = ""
    scope: str = ""
    key: str = ""


@dataclass
class MemoryUpdated(MemoryEvent):
    previous_value: str = ""
    new_value: str = ""


@dataclass
class MemoryMerged(MemoryEvent):
    source_memory_ids: list[str] = field(default_factory=list)


@dataclass
class MemoryArchived(MemoryEvent):
    reason: str = ""


@dataclass
class MemoryExpired(MemoryEvent):
    reason: str = "retention_reached"


@dataclass
class MemoryDeleted(MemoryEvent):
    reason: str = ""


@dataclass
class MemoryRestored(MemoryEvent):
    reason: str = ""


@dataclass
class MemoryConfidenceChanged(MemoryEvent):
    previous_confidence: str = ""
    new_confidence: str = ""


@dataclass
class MemoryImportanceChanged(MemoryEvent):
    previous_importance: str = ""
    new_importance: str = ""
