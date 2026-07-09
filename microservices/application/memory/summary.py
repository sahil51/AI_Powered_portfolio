from collections import Counter
from dataclasses import dataclass, field

from domain.memory.repository import MemoryRepository


@dataclass
class MemorySummaryStats:
    total_count: int = 0
    active_count: int = 0
    archived_count: int = 0
    expired_count: int = 0
    deleted_count: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    by_scope: dict[str, int] = field(default_factory=dict)
    by_priority: dict[str, int] = field(default_factory=dict)
    by_confidence: dict[str, int] = field(default_factory=dict)
    by_importance: dict[str, int] = field(default_factory=dict)
    by_source: dict[str, int] = field(default_factory=dict)
    top_tags: list[tuple[str, int]] = field(default_factory=list)


class MemorySummaryService:
    def __init__(self, repository: MemoryRepository) -> None:
        self._repository = repository

    async def get_user_summary(self, user_id: str) -> MemorySummaryStats:
        all_memories, _ = await self._repository.search_advanced(user_id=user_id, limit=10000)
        return self._build_summary(list(all_memories))

    async def get_conversation_summary(self, conversation_id: str) -> MemorySummaryStats:
        all_memories, _ = await self._repository.search_advanced(conversation_id=conversation_id, limit=10000)
        return self._build_summary(list(all_memories))

    async def get_global_summary(self) -> MemorySummaryStats:
        all_memories, _ = await self._repository.search_advanced(limit=10000)
        return self._build_summary(list(all_memories))

    def _build_summary(self, memories: list) -> MemorySummaryStats:
        stats = MemorySummaryStats(total_count=len(memories))
        categories: Counter = Counter()
        scopes: Counter = Counter()
        priorities: Counter = Counter()
        confidences: Counter = Counter()
        importances: Counter = Counter()
        sources: Counter = Counter()
        all_tags: Counter = Counter()

        for m in memories:
            categories[m.category.value if hasattr(m.category, "value") else str(m.category)] += 1
            scopes[m.scope.value if hasattr(m.scope, "value") else str(m.scope)] += 1
            priorities[m.priority.value if hasattr(m.priority, "value") else str(m.priority)] += 1
            confidences[m.confidence.value if hasattr(m.confidence, "value") else str(m.confidence)] += 1
            importances[m.importance.value if hasattr(m.importance, "value") else str(m.importance)] += 1
            sources[m.source.value if hasattr(m.source, "value") else str(m.source)] += 1

            status = m.status.value if hasattr(m.status, "value") else str(m.status)
            if status == "active" or status == "updated" or status == "merged":
                stats.active_count += 1
            elif status == "archived":
                stats.archived_count += 1
            elif status == "expired":
                stats.expired_count += 1
            elif status == "deleted":
                stats.deleted_count += 1

            for tag in m.tags:
                all_tags[tag] += 1

        stats.by_category = dict(categories)
        stats.by_scope = dict(scopes)
        stats.by_priority = dict(priorities)
        stats.by_confidence = dict(confidences)
        stats.by_importance = dict(importances)
        stats.by_source = dict(sources)
        stats.top_tags = all_tags.most_common(20)
        return stats

    async def get_memory_detail_summary(self, memory_id: str) -> dict | None:
        memory = await self._repository.get_by_id_str(memory_id)
        if memory is None:
            return None
        return {
            "memory_id": str(memory.memory_id),
            "user_id": memory.user_id,
            "category": memory.category.value,
            "scope": memory.scope.value,
            "status": memory.status.value,
            "priority": memory.priority.value,
            "confidence": memory.confidence.value,
            "importance": memory.importance.value,
            "source": memory.source.value,
            "tags": memory.tags,
            "record_count": memory.record_count,
            "version": memory.version,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
            "expires_at": memory.expires_at.isoformat() if memory.expires_at else None,
        }
