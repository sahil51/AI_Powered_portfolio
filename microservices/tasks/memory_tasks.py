from infrastructure.queue.celery_app import celery_app
from tasks.base import AppBaseTask


@celery_app.task(bind=True, base=AppBaseTask, queue="memory")
def update_conversation_summary_task(self, conversation_id: str, messages: list) -> dict:
    return {"status": "updated", "conversation_id": conversation_id}


@celery_app.task(bind=True, base=AppBaseTask, queue="memory")
def cleanup_expired_sessions_task(self) -> dict:
    return {"status": "cleanup_completed"}
