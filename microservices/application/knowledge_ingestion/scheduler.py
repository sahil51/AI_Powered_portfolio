from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from enum import Enum

from application.knowledge_ingestion.exceptions import SchedulerError
from application.knowledge_ingestion.models import (
    ImportSource,
    KnowledgeImportResult,
)
from application.knowledge_ingestion.service import KnowledgeIngestionService


class SchedulePriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class ScheduleStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledImport:
    def __init__(
        self,
        sources: list[ImportSource],
        schedule_at: datetime | None = None,
        priority: SchedulePriority = SchedulePriority.NORMAL,
        correlation_id: str = "",
        tags: list[str] | None = None,
        max_retries: int = 3,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.sources = sources
        self.schedule_at = schedule_at or datetime.utcnow()
        self.priority = priority
        self.correlation_id = correlation_id
        self.tags = tags or []
        self.max_retries = max_retries
        self.retry_count = 0
        self.status = ScheduleStatus.PENDING
        self.results: list[KnowledgeImportResult] = []
        self.created_at = datetime.utcnow()
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.error: str = ""


class KnowledgeScheduler:
    def __init__(self, ingestion_service: KnowledgeIngestionService) -> None:
        self._ingestion_service = ingestion_service
        self._scheduled_jobs: dict[str, ScheduledImport] = {}
        self._job_queue: list[str] = []

    def schedule(
        self,
        sources: list[ImportSource],
        schedule_at: datetime | None = None,
        priority: SchedulePriority = SchedulePriority.NORMAL,
        correlation_id: str = "",
        tags: list[str] | None = None,
        max_retries: int = 3,
    ) -> str:
        job = ScheduledImport(
            sources=sources,
            schedule_at=schedule_at,
            priority=priority,
            correlation_id=correlation_id,
            tags=tags,
            max_retries=max_retries,
        )
        job.status = ScheduleStatus.SCHEDULED
        self._scheduled_jobs[job.id] = job
        self._job_queue.append(job.id)
        self._job_queue.sort(
            key=lambda jid: (
                self._scheduled_jobs[jid].schedule_at,
                -self._scheduled_jobs[jid].priority.value,
            )
        )
        return job.id

    async def execute_pending(self) -> list[KnowledgeImportResult]:
        now = datetime.utcnow()
        all_results: list[KnowledgeImportResult] = []
        ready_ids = [
            jid
            for jid in self._job_queue
            if self._scheduled_jobs[jid].schedule_at <= now
            and self._scheduled_jobs[jid].status == ScheduleStatus.SCHEDULED
        ]

        for jid in ready_ids:
            job = self._scheduled_jobs[jid]
            results = await self._execute_job(job)
            all_results.extend(results)

        return all_results

    async def _execute_job(self, job: ScheduledImport) -> list[KnowledgeImportResult]:
        job.status = ScheduleStatus.RUNNING
        job.started_at = datetime.utcnow()

        try:
            results = await self._ingestion_service.import_batch(
                sources=job.sources,
                correlation_id=job.correlation_id,
                tags=job.tags,
            )
            job.results = results
            success_count = sum(1 for r in results if r.success)
            if success_count == len(results):
                job.status = ScheduleStatus.COMPLETED
            else:
                job.status = ScheduleStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            return results
        except Exception as e:
            job.error = str(e)
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.schedule_at = datetime.utcnow() + timedelta(
                    minutes=2**job.retry_count * 5
                )
                job.status = ScheduleStatus.SCHEDULED
            else:
                job.status = ScheduleStatus.FAILED
                job.completed_at = datetime.utcnow()
            return job.results

    def cancel_job(self, job_id: str) -> None:
        if job_id not in self._scheduled_jobs:
            raise SchedulerError(f"Job not found: {job_id}")
        job = self._scheduled_jobs[job_id]
        job.status = ScheduleStatus.CANCELLED
        job.completed_at = datetime.utcnow()

    def get_job(self, job_id: str) -> ScheduledImport | None:
        return self._scheduled_jobs.get(job_id)

    def get_pending_count(self) -> int:
        return sum(
            1 for j in self._scheduled_jobs.values() if j.status == ScheduleStatus.SCHEDULED
        )

    def get_failed_jobs(self) -> list[ScheduledImport]:
        return [j for j in self._scheduled_jobs.values() if j.status == ScheduleStatus.FAILED]
