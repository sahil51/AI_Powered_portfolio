from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from domain.knowledge.value_objects import DocumentId


class EmbeddingScheduleStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class EmbeddingScheduleItem:
    item_id: str = ""
    document_id: DocumentId | None = None
    status: EmbeddingScheduleStatus = EmbeddingScheduleStatus.PENDING
    priority: int = 0
    created_at: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class EmbeddingScheduler:
    def __init__(self) -> None:
        self._items: dict[str, EmbeddingScheduleItem] = {}
        self._queue: list[str] = []

    def schedule(self, document_id: DocumentId, priority: int = 0) -> EmbeddingScheduleItem:
        item_id = f"emb_{document_id}_{int(time.monotonic() * 1000)}"
        item = EmbeddingScheduleItem(
            item_id=item_id,
            document_id=document_id,
            status=EmbeddingScheduleStatus.PENDING,
            priority=priority,
            created_at=time.monotonic(),
        )
        self._items[item_id] = item
        self._queue.append(item_id)
        self._queue.sort(key=lambda x: self._items[x].priority, reverse=True)
        return item

    def start_next(self) -> EmbeddingScheduleItem | None:
        while self._queue:
            item_id = self._queue.pop(0)
            item = self._items.get(item_id)
            if item is None or item.status == EmbeddingScheduleStatus.CANCELLED:
                continue
            item.status = EmbeddingScheduleStatus.IN_PROGRESS
            item.started_at = time.monotonic()
            return item
        return None

    def complete(self, item_id: str) -> None:
        item = self._items.get(item_id)
        if item:
            item.status = EmbeddingScheduleStatus.COMPLETED
            item.completed_at = time.monotonic()

    def fail(self, item_id: str, error: str) -> None:
        item = self._items.get(item_id)
        if item:
            item.status = EmbeddingScheduleStatus.FAILED
            item.error = error
            item.completed_at = time.monotonic()

    def cancel(self, item_id: str) -> bool:
        item = self._items.get(item_id)
        if not item:
            return False
        item.status = EmbeddingScheduleStatus.CANCELLED
        item.completed_at = time.monotonic()
        if item_id in self._queue:
            self._queue.remove(item_id)
        return True

    def get_status(self, item_id: str) -> EmbeddingScheduleStatus | None:
        item = self._items.get(item_id)
        return item.status if item else None

    def get_queue_depth(self) -> int:
        return len(self._queue)

    def list_by_status(self, status: EmbeddingScheduleStatus) -> list[EmbeddingScheduleItem]:
        return [item for item in self._items.values() if item.status == status]

    def clear_completed(self) -> None:
        self._items = {
            k: v for k, v in self._items.items()
            if v.status in (EmbeddingScheduleStatus.PENDING, EmbeddingScheduleStatus.IN_PROGRESS)
        }
        self._queue = [i for i in self._queue if i in self._items]
