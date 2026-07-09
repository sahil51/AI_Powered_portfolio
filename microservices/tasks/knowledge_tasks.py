from __future__ import annotations

import asyncio
import uuid
from typing import Any

from celery import Task, current_app
from celery.utils.log import get_task_logger

from application.knowledge_ingestion.models import ImportSource, ImportSourceType
from application.knowledge_ingestion.service import KnowledgeIngestionService
from tasks.base import AppBaseTask

logger = get_task_logger(__name__)

_service: KnowledgeIngestionService | None = None


def _get_service() -> KnowledgeIngestionService:
    global _service
    if _service is None:
        from application.di.container import container
        _service = container.resolve(KnowledgeIngestionService)
    return _service


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


@current_app.task(
    bind=True,
    base=AppBaseTask,
    queue="default",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    name="knowledge.import_document",
)
def import_document_task(
    self: Task,
    source_type: str,
    filename: str = "",
    file_path: str = "",
    url: str = "",
    content: str = "",
    mime_type: str = "",
    size_bytes: int = 0,
    doc_type: str = "",
    correlation_id: str = "",
    tags: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    service = _get_service()
    correlation_id = correlation_id or str(uuid.uuid4())

    source = ImportSource(
        source_type=ImportSourceType(source_type),
        filename=filename,
        file_path=file_path,
        url=url,
        content=content,
        mime_type=mime_type,
        size_bytes=size_bytes,
    )

    from domain.knowledge.value_objects import DocumentType
    resolved_doc_type = DocumentType(doc_type) if doc_type else None

    result = _run_async(
        service.import_document(
            source=source,
            doc_type=resolved_doc_type,
            correlation_id=correlation_id,
            tags=tags or [],
            **kwargs,
        )
    )

    return {
        "success": result.success,
        "document_id": str(result.document_id) if result.document_id else None,
        "error": result.error,
        "chunk_count": result.chunk_count,
        "version": result.version,
        "latency_ms": result.latency_ms,
        "correlation_id": result.correlation_id,
    }


@current_app.task(
    bind=True,
    base=AppBaseTask,
    queue="default",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    name="knowledge.import_batch",
)
def import_batch_task(
    self: Task,
    items: list[dict[str, Any]],
    correlation_id: str = "",
    tags: list[str] | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in items:
        result = import_document_task(
            source_type=item.get("source_type", "file_upload"),
            filename=item.get("filename", ""),
            file_path=item.get("file_path", ""),
            url=item.get("url", ""),
            content=item.get("content", ""),
            mime_type=item.get("mime_type", ""),
            size_bytes=item.get("size_bytes", 0),
            doc_type=item.get("doc_type", ""),
            correlation_id=correlation_id,
            tags=tags,
        )
        results.append(result)
    return results


@current_app.task(
    bind=True,
    base=AppBaseTask,
    queue="default",
    name="knowledge.reprocess_document",
)
def reprocess_document_task(
    self: Task,
    document_id: str,
    correlation_id: str = "",
) -> dict[str, Any]:
    from application.di.container import container
    from domain.knowledge.repository import KnowledgeRepository

    service = _get_service()
    correlation_id = correlation_id or str(uuid.uuid4())

    def _run() -> dict[str, Any]:
        import asyncio
        async def _inner() -> dict[str, Any]:
            repo = container.resolve(KnowledgeRepository)
            doc = await repo.get_by_id_str(document_id)
            if doc is None:
                return {"success": False, "error": f"Document not found: {document_id}"}

            source = ImportSource(
                source_type=ImportSourceType.FILE_UPLOAD,
                filename=doc.title,
                content=doc.title,
                mime_type="text/plain",
            )

            result = await service.import_document(
                source=source,
                doc_type=doc.doc_type,
                correlation_id=correlation_id,
            )

            return {
                "success": result.success,
                "document_id": str(result.document_id) if result.document_id else None,
                "error": result.error,
                "chunk_count": result.chunk_count,
                "version": result.version,
                "latency_ms": result.latency_ms,
                "correlation_id": result.correlation_id,
            }
        return asyncio.run(_inner())

    try:
        return _run()
    except Exception as e:
        return {"success": False, "error": str(e)}


@current_app.task(
    bind=True,
    base=AppBaseTask,
    queue="default",
    name="knowledge.schedule_ingestion",
)
def schedule_ingestion_task(
    self: Task,
    job_id: str,
) -> dict[str, Any]:
    from application.di.container import container
    from application.knowledge_ingestion.scheduler import KnowledgeScheduler

    scheduler = container.resolve(KnowledgeScheduler)
    results = scheduler.execute_pending()

    return {
        "job_id": job_id,
        "results_count": len(results),
        "success_count": sum(1 for r in results if r.success),
        "failed_count": sum(1 for r in results if not r.success),
    }


@current_app.task(
    bind=True,
    base=AppBaseTask,
    queue="default",
    name="knowledge.cancel_ingestion",
)
def cancel_ingestion_task(
    self: Task,
    job_id: str,
) -> dict[str, Any]:
    from application.di.container import container
    from application.knowledge_ingestion.scheduler import KnowledgeScheduler

    scheduler = container.resolve(KnowledgeScheduler)
    try:
        scheduler.cancel_job(job_id)
        return {"success": True, "job_id": job_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


@current_app.task(
    bind=True,
    base=AppBaseTask,
    queue="default",
    name="knowledge.cleanup_dead_letters",
)
def cleanup_dead_letters_task(self: Task) -> dict[str, Any]:
    from application.di.container import container
    from application.knowledge_ingestion.scheduler import KnowledgeScheduler

    scheduler = container.resolve(KnowledgeScheduler)
    failed = scheduler.get_failed_jobs()

    cleaned = 0
    for job in failed:
        if job.retry_count >= job.max_retries:
            cleaned += 1

    return {
        "dead_letter_count": len(failed),
        "cleaned": cleaned,
    }
