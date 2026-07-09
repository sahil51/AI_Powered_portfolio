from datetime import datetime, timezone

from domain.memory.aggregate import Memory
from domain.memory.policies import MemoryPolicies, default_policies
from domain.memory.state import MemoryStatus


class MemoryLifecycle:
    def __init__(self, policies: MemoryPolicies | None = None) -> None:
        self._policies = policies or default_policies

    def should_expire(self, memory: Memory) -> bool:
        if memory.status == MemoryStatus.DELETED:
            return False
        elapsed = memory.elapsed_since_created()
        return self._policies.retention_exceeded(elapsed)

    def should_archive(self, memory: Memory) -> bool:
        if memory.is_terminal:
            return False
        if not memory.is_active:
            return False
        elapsed = memory.elapsed_since_updated()
        return self._policies.retention_exceeded(elapsed)

    def should_purge(self, memory: Memory) -> bool:
        if memory.status != MemoryStatus.DELETED:
            return False
        elapsed = memory.elapsed_since_updated()
        return self._policies.max_retention_exceeded(elapsed)

    def can_update_confidence(self, memory: Memory, new_confidence: object) -> bool:
        return memory.can_modify

    def can_update_importance(self, memory: Memory, new_importance: object) -> bool:
        return memory.can_modify

    def is_expired(self, memory: Memory) -> bool:
        if memory.expires_at is None:
            return False
        return datetime.now(timezone.utc) > memory.expires_at
