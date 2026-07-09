from domain.memory.aggregate import Memory
from domain.memory.policies import MemoryPolicies, default_policies
from domain.memory.value_objects import (
    MemoryCategory,
    MemoryConfidence,
    MemoryImportance,
    MemoryPriority,
    MemoryScope,
    MemorySource,
)


class MemoryValidationError(Exception):
    pass


class MemoryValidator:
    def __init__(self, policies: MemoryPolicies | None = None) -> None:
        self._policies = policies or default_policies

    def validate_create(
        self,
        user_id: str,
        category: MemoryCategory,
        scope: MemoryScope,
        value: str,
    ) -> None:
        if not user_id:
            raise MemoryValidationError("User ID is required")
        if not value:
            raise MemoryValidationError("Memory value is required")
        if category not in MemoryCategory:
            raise MemoryValidationError(f"Invalid memory category: {category}")

    def validate_value(self, value: str) -> None:
        if not value or not value.strip():
            raise MemoryValidationError("Memory value cannot be empty")
        if len(value) > 100000:
            raise MemoryValidationError("Memory value exceeds maximum length of 100000 characters")

    def validate_confidence(self, confidence: MemoryConfidence) -> None:
        if confidence not in MemoryConfidence:
            raise MemoryValidationError(f"Invalid confidence level: {confidence}")

    def validate_priority(self, priority: MemoryPriority) -> None:
        if priority not in MemoryPriority:
            raise MemoryValidationError(f"Invalid priority: {priority}")

    def validate_importance(self, importance: MemoryImportance) -> None:
        if importance not in MemoryImportance:
            raise MemoryValidationError(f"Invalid importance: {importance}")

    def validate_source(self, source: MemorySource) -> None:
        if source not in MemorySource:
            raise MemoryValidationError(f"Invalid memory source: {source}")

    def validate_scope(self, scope: MemoryScope) -> None:
        if scope not in MemoryScope:
            raise MemoryValidationError(f"Invalid memory scope: {scope}")

    def validate_category(self, category: MemoryCategory) -> None:
        if category not in MemoryCategory:
            raise MemoryValidationError(f"Invalid memory category: {category}")

    def validate_ownership(self, memory: Memory, user_id: str) -> bool:
        return memory.user_id == user_id

    def validate_duplicate(self, existing_value: str | None, new_value: str) -> bool:
        if existing_value is None:
            return True
        return existing_value != new_value

    def validate_expiry(self, expires_at: object | None) -> bool:
        if expires_at is None:
            return True
        from datetime import datetime, timezone
        if isinstance(expires_at, datetime):
            return expires_at > datetime.now(timezone.utc)
        return True

    def validate_retention(self, elapsed_days: float) -> bool:
        return not self._policies.retention_exceeded(elapsed_days)
