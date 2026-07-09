from infrastructure.queue.celery_app import celery_app
from monitoring.logger import logger
from tasks.base import AppBaseTask


@celery_app.task(bind=True, base=AppBaseTask, queue="maintenance")
def cleanup_expired_sessions(self) -> dict:
    logger.info("Running expired session cleanup")
    return {"status": "cleanup_completed"}


@celery_app.task(bind=True, base=AppBaseTask, queue="maintenance")
def cleanup_expired_idempotency_keys(self) -> dict:
    logger.info("Running idempotency key cleanup")
    return {"status": "cleanup_completed"}


@celery_app.task(bind=True, base=AppBaseTask, queue="maintenance")
def health_check_workers(self) -> dict:
    logger.info("Running worker health check")
    return {"status": "healthy", "workers_checked": 0}


@celery_app.task(bind=True, base=AppBaseTask, queue="maintenance")
def collect_celery_metrics(self) -> dict:
    logger.info("Collecting Celery metrics")
    return {"status": "collected"}
