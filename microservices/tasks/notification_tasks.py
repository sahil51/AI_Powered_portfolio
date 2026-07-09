from infrastructure.queue.celery_app import celery_app
from monitoring.logger import logger
from tasks.base import AppBaseTask


@celery_app.task(bind=True, base=AppBaseTask, queue="notifications")
def create_lead_task(self, lead_data: dict) -> dict:
    try:
        logger.info("Creating lead", extra={"data": lead_data})
        return {
            "status": "created",
            "lead_name": lead_data.get("full_name"),
            "message": "Lead created successfully. n8n will handle CRM and notifications.",
        }
    except Exception as exc:
        logger.error(f"Lead creation failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, base=AppBaseTask, queue="notifications")
def send_notification_task(self, notification_type: str, data: dict) -> dict:
    return {"status": "sent", "type": notification_type}


@celery_app.task(bind=True, base=AppBaseTask, queue="notifications")
def send_followup_task(self, meeting_id: str) -> dict:
    return {"status": "followup_scheduled", "meeting_id": meeting_id}
