from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from domain.memory.aggregate import Memory
from domain.memory.value_objects import MemoryConfidence, MemoryImportance


class MemorySortField(str, Enum):
    IMPORTANCE = "importance"
    CONFIDENCE = "confidence"
    PRIORITY = "priority"
    RECENCY = "recency"
    ACCESS_COUNT = "access_count"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class MemorySortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class MemoryFilter:
    user_id: str | None = None
    conversation_id: str | None = None
    session_id: str | None = None
    category: str | None = None
    scope: str | None = None
    priority: str | None = None
    confidence: str | None = None
    importance: str | None = None
    source: str | None = None
    status: str | None = None
    tags: list[str] | None = None
    query: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    active_only: bool = True

    def to_repo_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        for field_name in ("user_id", "conversation_id", "session_id", "category",
                           "scope", "priority", "confidence", "importance",
                           "source", "status", "tags", "query", "date_from", "date_to"):
            value = getattr(self, field_name)
            if value is not None:
                kwargs[field_name] = value
        return kwargs


@dataclass
class MemorySort:
    field: MemorySortField = MemorySortField.RECENCY
    order: MemorySortOrder = MemorySortOrder.DESC

    @property
    def sort_by(self) -> str:
        mapping = {
            MemorySortField.IMPORTANCE: "importance",
            MemorySortField.CONFIDENCE: "confidence",
            MemorySortField.PRIORITY: "priority",
            MemorySortField.RECENCY: "last_activity_at",
            MemorySortField.ACCESS_COUNT: "access_count",
            MemorySortField.CREATED_AT: "created_at",
            MemorySortField.UPDATED_AT: "updated_at",
        }
        return mapping.get(self.field, "last_activity_at")

    @property
    def sort_desc(self) -> bool:
        return self.order == MemorySortOrder.DESC


@dataclass
class MemoryPage:
    skip: int = 0
    limit: int = 20

    @property
    def next_skip(self) -> int:
        return self.skip + self.limit


@dataclass
class MemoryResult:
    items: list[Memory] = field(default_factory=list)
    total: int = 0
    skip: int = 0
    limit: int = 20

    @property
    def has_more(self) -> bool:
        return (self.skip + self.limit) < self.total

    @property
    def page_count(self) -> int:
        if self.limit == 0:
            return 0
        return (self.total + self.limit - 1) // self.limit

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "skip": self.skip,
            "limit": self.limit,
            "has_more": self.has_more,
            "page_count": self.page_count,
            "count": len(self.items),
            "items": [
                {
                    "memory_id": str(m.memory_id),
                    "category": m.category.value,
                    "scope": m.scope.value,
                    "status": m.status.value,
                    "priority": m.priority.value,
                    "confidence": m.confidence.value,
                    "importance": m.importance.value,
                    "tags": m.tags,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                }
                for m in self.items
            ],
        }


PRIORITY_ORDER: dict[str, int] = {
    "critical": 0, "high": 1, "medium": 2, "low": 3, "background": 4,
}

CONFIDENCE_ORDER: dict[str, int] = {
    "certain": 0, "high": 1, "medium": 2, "low": 3, "inferred": 4, "uncertain": 5,
}

IMPORTANCE_ORDER: dict[str, int] = {
    "critical": 0, "high": 1, "medium": 2, "low": 3, "trivial": 4,
}


class MemoryRankingEngine:
    def rank(self, memories: list[Memory], sort: MemorySort | None = None) -> list[Memory]:
        if sort is None:
            return self._rank_by_business_rules(memories)

        if sort.field == MemorySortField.IMPORTANCE:
            return sorted(memories, key=lambda m: IMPORTANCE_ORDER.get(m.importance.value, 99),
                          reverse=not sort.sort_desc)
        elif sort.field == MemorySortField.CONFIDENCE:
            return sorted(memories, key=lambda m: CONFIDENCE_ORDER.get(m.confidence.value, 99),
                          reverse=not sort.sort_desc)
        elif sort.field == MemorySortField.PRIORITY:
            return sorted(memories, key=lambda m: PRIORITY_ORDER.get(m.priority.value, 99),
                          reverse=not sort.sort_desc)
        elif sort.field == MemorySortField.RECENCY:
            return sorted(memories, key=lambda m: m.updated_at or datetime.min.replace(tzinfo=timezone.utc),
                          reverse=sort.sort_desc)
        elif sort.field == MemorySortField.ACCESS_COUNT:
            return sorted(memories, key=lambda m: getattr(m, "access_count", 0), reverse=sort.sort_desc)
        return memories

    def _rank_by_business_rules(self, memories: list[Memory]) -> list[Memory]:
        def score(m: Memory) -> float:
            imp = IMPORTANCE_ORDER.get(m.importance.value, 99)
            conf = CONFIDENCE_ORDER.get(m.confidence.value, 99)
            pri = PRIORITY_ORDER.get(m.priority.value, 99)
            return imp * 10000 + conf * 100 + pri

        return sorted(memories, key=score)


class MemoryFilterEngine:
    def apply(self, memories: list[Memory], filter_obj: MemoryFilter | None = None) -> list[Memory]:
        if filter_obj is None:
            return memories
        result = list(memories)

        if filter_obj.active_only and not filter_obj.status:
            result = [m for m in result if m.is_active or m.status.value == "created"]

        if filter_obj.category:
            result = [m for m in result if m.category.value == filter_obj.category]
        if filter_obj.scope:
            result = [m for m in result if m.scope.value == filter_obj.scope]
        if filter_obj.priority:
            result = [m for m in result if m.priority.value == filter_obj.priority]
        if filter_obj.confidence:
            result = [m for m in result if m.confidence.value == filter_obj.confidence]
        if filter_obj.importance:
            result = [m for m in result if m.importance.value == filter_obj.importance]
        if filter_obj.source:
            result = [m for m in result if m.source.value == filter_obj.source]
        if filter_obj.status:
            result = [m for m in result if m.status.value == filter_obj.status]
        if filter_obj.tags:
            result = [m for m in result if any(t in m.tags for t in filter_obj.tags)]
        if filter_obj.query:
            q = filter_obj.query.lower()
            result = [m for m in result if q in m.value.lower()]

        return result


class MemorySelectionEngine:
    def __init__(self, ranking_engine: MemoryRankingEngine | None = None) -> None:
        self._ranking = ranking_engine or MemoryRankingEngine()

    def select_top(self, memories: list[Memory], count: int, sort: MemorySort | None = None) -> list[Memory]:
        ranked = self._ranking.rank(memories, sort)
        return ranked[:count]

    def select_by_importance(self, memories: list[Memory], min_importance: MemoryImportance) -> list[Memory]:
        levels = list(MemoryImportance)
        threshold = levels.index(min_importance)
        return [m for m in memories if levels.index(m.importance) <= threshold]

    def select_by_confidence(self, memories: list[Memory], min_confidence: MemoryConfidence) -> list[Memory]:
        levels = list(MemoryConfidence)
        threshold = levels.index(min_confidence)
        return [m for m in memories if levels.index(m.confidence) <= threshold]


class MemoryQueryEngine:
    def __init__(
        self,
        ranking: MemoryRankingEngine | None = None,
        filtering: MemoryFilterEngine | None = None,
        selection: MemorySelectionEngine | None = None,
    ) -> None:
        self._ranking = ranking or MemoryRankingEngine()
        self._filtering = filtering or MemoryFilterEngine()
        self._selection = selection or MemorySelectionEngine(self._ranking)

    def execute(
        self,
        memories: list[Memory],
        filter_obj: MemoryFilter | None = None,
        sort: MemorySort | None = None,
        page: MemoryPage | None = None,
    ) -> MemoryResult:
        filtered = self._filtering.apply(memories, filter_obj)
        ranked = self._ranking.rank(filtered, sort)

        page = page or MemoryPage()
        total = len(ranked)
        paged = ranked[page.skip:page.skip + page.limit]

        return MemoryResult(items=paged, total=total, skip=page.skip, limit=page.limit)
