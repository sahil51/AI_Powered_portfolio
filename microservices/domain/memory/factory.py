from domain.memory.aggregate import Memory
from domain.memory.policies import MemoryPolicies, default_policies
from domain.memory.state import MemoryStateMachine, MemoryStatus
from domain.memory.validator import MemoryValidator
from domain.memory.value_objects import (
    MemoryCategory,
    MemoryConfidence,
    MemoryId,
    MemoryImportance,
    MemoryKey,
    MemoryPriority,
    MemoryScope,
    MemorySource,
)


class MemoryFactory:
    def __init__(self, validator: MemoryValidator | None = None) -> None:
        self._validator = validator or MemoryValidator()

    def create(
        self,
        user_id: str,
        value: str,
        category: MemoryCategory = MemoryCategory.FACT,
        scope: MemoryScope = MemoryScope.USER,
        key: MemoryKey | None = None,
        conversation_id: str | None = None,
        session_id: str | None = None,
        memory_type: str = "fact",
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        confidence: MemoryConfidence = MemoryConfidence.MEDIUM,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        source: MemorySource = MemorySource.SYSTEM,
        policies: MemoryPolicies | None = None,
        correlation_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> Memory:
        self._validator.validate_create(user_id, category, scope, value)
        self._validator.validate_value(value)

        memory = Memory(
            memory_id=MemoryId(),
            user_id=user_id,
            conversation_id=conversation_id,
            session_id=session_id,
            key=key,
            value=value,
            memory_type=memory_type,
            category=category,
            scope=scope,
            priority=priority,
            confidence=confidence,
            importance=importance,
            source=source,
            state_machine=MemoryStateMachine(),
            tags=tags or [],
            metadata=metadata or {},
            policies=policies or default_policies,
            correlation_id=correlation_id,
        )

        memory.activate()
        return memory

    def restore(
        self,
        memory_id: str,
        user_id: str,
        value: str,
        category: MemoryCategory,
        scope: MemoryScope,
        status: str = "active",
        key: MemoryKey | None = None,
        conversation_id: str | None = None,
        session_id: str | None = None,
        memory_type: str = "fact",
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        confidence: MemoryConfidence = MemoryConfidence.MEDIUM,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        source: MemorySource = MemorySource.SYSTEM,
        tags: list[str] | None = None,
        metadata: dict | None = None,
        correlation_id: str | None = None,
        expires_at: object = None,
        created_at: object = None,
        updated_at: object = None,
        version: int = 1,
    ) -> Memory:
        import datetime

        mid = MemoryId()
        mid.__dict__["value"] = memory_id

        mem = Memory(
            memory_id=mid,
            user_id=user_id,
            conversation_id=conversation_id,
            session_id=session_id,
            key=key,
            value=value,
            memory_type=memory_type,
            category=category,
            scope=scope,
            priority=priority,
            confidence=confidence,
            importance=importance,
            source=source,
            state_machine=MemoryStateMachine(MemoryStatus(status)),
            tags=tags or [],
            metadata=metadata or {},
            correlation_id=correlation_id,
            expires_at=expires_at,
            created_at=created_at or datetime.datetime.now(datetime.timezone.utc),
            updated_at=updated_at or datetime.datetime.now(datetime.timezone.utc),
            version=version,
        )
        return mem
