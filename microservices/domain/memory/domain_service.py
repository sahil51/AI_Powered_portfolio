from domain.memory.aggregate import Memory
from domain.memory.lifecycle import MemoryLifecycle
from domain.memory.policies import MemoryPolicies, default_policies
from domain.memory.state import MemoryStatus
from domain.memory.validator import MemoryValidator


class MemoryDomainService:
    def __init__(
        self,
        validator: MemoryValidator | None = None,
        policies: MemoryPolicies | None = None,
        lifecycle: MemoryLifecycle | None = None,
    ) -> None:
        self._validator = validator or MemoryValidator()
        self._policies = policies or default_policies
        self._lifecycle = lifecycle or MemoryLifecycle(policies)

    def resolve_conflict(
        self,
        existing: Memory,
        incoming: Memory,
    ) -> Memory:
        if self._policies.can_overwrite(existing.confidence, incoming.confidence):
            existing.update_value(incoming.value, incoming.confidence)
            return existing
        return existing

    def can_add_memory(self, memory: Memory, current_count: int) -> bool:
        if self._policies.exceeds_scope_limit(current_count, memory.scope):
            return False
        return True

    def should_notify(self, memory: Memory) -> bool:
        return self._policies.should_notify_importance(memory.importance)

    def qualifies_for_persist(self, memory: Memory) -> bool:
        return self._policies.is_confidence_sufficient(memory.confidence)

    def evaluate_retention(self, memory: Memory) -> MemoryStatus | None:
        if self._lifecycle.should_expire(memory):
            return MemoryStatus.EXPIRED
        if self._lifecycle.should_archive(memory):
            return MemoryStatus.ARCHIVED
        if self._lifecycle.should_purge(memory):
            return MemoryStatus.DELETED
        return None
