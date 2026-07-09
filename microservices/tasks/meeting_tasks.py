from infrastructure.queue.celery_app import celery_app
from monitoring.logger import logger
from tasks.base import AppBaseTask


@celery_app.task(bind=True, base=AppBaseTask, queue="meetings", max_retries=3, default_retry_delay=60)
def schedule_meeting_task(self, meeting_data: dict) -> dict:
    try:
        logger.info("Scheduling meeting", extra={"data": meeting_data})
        return {
            "status": "scheduled",
            "meeting_type": meeting_data.get("meeting_type"),
            "message": "Meeting scheduled successfully. n8n will handle calendar, email, and CRM.",
        }
    except Exception as exc:
        logger.error(f"Meeting scheduling failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, base=AppBaseTask, queue="meetings")
def check_availability_task(self, date: str, time: str, timezone: str) -> dict:
    return {"available": True, "suggested_slots": []}


@celery_app.task(bind=True, base=AppBaseTask, queue="meetings")
def cancel_meeting_task(self, meeting_id: str) -> dict:
    return {"status": "cancelled", "meeting_id": meeting_id}
