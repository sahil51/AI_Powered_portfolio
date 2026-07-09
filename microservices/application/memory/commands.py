from dataclasses import dataclass
from typing import Any

from domain.memory.value_objects import (
    MemoryCategory,
    MemoryConfidence,
    MemoryImportance,
    MemoryKey,
    MemoryPriority,
    MemoryScope,
    MemorySource,
)


@dataclass
class CreateMemoryCommand:
    user_id: str
    value: str
    category: MemoryCategory = MemoryCategory.FACT
    scope: MemoryScope = MemoryScope.USER
    key: MemoryKey | None = None
    conversation_id: str | None = None
    session_id: str | None = None
    memory_type: str = "fact"
    priority: MemoryPriority = MemoryPriority.MEDIUM
    confidence: MemoryConfidence = MemoryConfidence.MEDIUM
    importance: MemoryImportance = MemoryImportance.MEDIUM
    source: MemorySource = MemorySource.USER_INPUT
    correlation_id: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class UpdateMemoryCommand:
    memory_id: str
    value: str
    confidence: MemoryConfidence | None = None
    user_id: str = ""


@dataclass
class MergeMemoryCommand:
    target_memory_id: str
    source_memory_id: str
    user_id: str = ""


@dataclass
class ArchiveMemoryCommand:
    memory_id: str
    reason: str = ""
    user_id: str = ""


@dataclass
class RestoreMemoryCommand:
    memory_id: str
    user_id: str = ""


@dataclass
class DeleteMemoryCommand:
    memory_id: str
    reason: str = ""
    user_id: str = ""


@dataclass
class ChangeConfidenceCommand:
    memory_id: str
    new_confidence: MemoryConfidence
    user_id: str = ""


@dataclass
class ChangeImportanceCommand:
    memory_id: str
    new_importance: MemoryImportance
    user_id: str = ""
