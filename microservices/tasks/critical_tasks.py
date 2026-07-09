from infrastructure.queue.celery_app import celery_app
from tasks.base import AppBaseTask


@celery_app.task(bind=True, base=AppBaseTask, queue="critical", max_retries=5, default_retry_delay=30)
def critical_operation_task(self, operation: str, data: dict) -> dict:
    return {"status": "completed", "operation": operation}


@celery_app.task(bind=True, base=AppBaseTask, queue="critical", max_retries=5, default_retry_delay=10)
def failover_task(self, service: str, error: dict) -> dict:
    return {"status": "failover_initiated", "service": service}
