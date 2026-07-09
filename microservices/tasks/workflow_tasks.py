from infrastructure.queue.celery_app import celery_app
from tasks.base import AppBaseTask


@celery_app.task(bind=True, base=AppBaseTask, queue="workflow")
def execute_workflow_task(self, workflow_type: str, data: dict) -> dict:
    return {"status": "executed", "workflow_type": workflow_type}


@celery_app.task(bind=True, base=AppBaseTask, queue="workflow")
def continue_workflow_task(self, workflow_id: str, step: str, result: dict) -> dict:
    return {"status": "continued", "workflow_id": workflow_id, "step": step}


@celery_app.task(bind=True, base=AppBaseTask, queue="workflow")
def fail_workflow_task(self, workflow_id: str, error: str) -> dict:
    return {"status": "failed", "workflow_id": workflow_id, "error": error}
