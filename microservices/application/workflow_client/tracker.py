from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from application.workflow_client.models import WorkflowOperation


class WorkflowTrackingStatus(str, Enum):
    PENDING = "pending"
    IN_FLIGHT = "in_flight"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class WorkflowTrackingRecord:
    correlation_id: str = ""
    operation: WorkflowOperation = WorkflowOperation.CUSTOM
    status: WorkflowTrackingStatus = WorkflowTrackingStatus.PENDING
    attempt: int = 0
    max_retries: int = 3
    started_at: float = 0.0
    completed_at: float = 0.0
    latency_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowStatusTracker:
    def __init__(self) -> None:
        self._records: dict[str, WorkflowTrackingRecord] = {}

    def start(self, correlation_id: str, operation: WorkflowOperation, max_retries: int = 3) -> WorkflowTrackingRecord:
        record = WorkflowTrackingRecord(
            correlation_id=correlation_id,
            operation=operation,
            status=WorkflowTrackingStatus.IN_FLIGHT,
            max_retries=max_retries,
            started_at=time.time(),
        )
        self._records[correlation_id] = record
        return record

    def complete(self, correlation_id: str, success: bool, latency_ms: float) -> WorkflowTrackingRecord | None:
        record = self._records.get(correlation_id)
        if not record:
            return None
        record.status = WorkflowTrackingStatus.SUCCEEDED if success else WorkflowTrackingStatus.FAILED
        record.completed_at = time.time()
        record.latency_ms = latency_ms
        return record

    def fail(self, correlation_id: str, error: str) -> WorkflowTrackingRecord | None:
        record = self._records.get(correlation_id)
        if not record:
            return None
        record.status = WorkflowTrackingStatus.FAILED
        record.error = error
        record.completed_at = time.time()
        return record

    def cancel(self, correlation_id: str) -> WorkflowTrackingRecord | None:
        record = self._records.get(correlation_id)
        if not record:
            return None
        record.status = WorkflowTrackingStatus.CANCELLED
        record.completed_at = time.time()
        return record

    def get(self, correlation_id: str) -> WorkflowTrackingRecord | None:
        return self._records.get(correlation_id)

    def list_active(self) -> list[WorkflowTrackingRecord]:
        return [
            r for r in self._records.values()
            if r.status == WorkflowTrackingStatus.IN_FLIGHT
        ]

    def list_by_operation(self, operation: WorkflowOperation) -> list[WorkflowTrackingRecord]:
        return [r for r in self._records.values() if r.operation == operation]

    def clear(self) -> None:
        self._records.clear()
