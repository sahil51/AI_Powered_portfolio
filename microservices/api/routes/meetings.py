from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from middleware.audit import log_audit
from middleware.auth import verify_token
from monitoring.logger import logger
from tasks.meeting_tasks import schedule_meeting_task

router = APIRouter(prefix="/meetings", tags=["Meetings"])


class MeetingScheduleRequest(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    contact_number: str = Field(..., min_length=7)
    company_name: str
    company_address: str
    meeting_purpose: str
    preferred_date: str
    preferred_time: str
    timezone: str
    meeting_type: str = Field(..., pattern="^(google_meet|phone_call|in_person)$")
    location: Optional[str] = None


class MeetingScheduleResponse(BaseModel):
    task_id: str
    status: str
    message: str


@router.post("/schedule", response_model=MeetingScheduleResponse)
async def schedule_meeting(
    request: MeetingScheduleRequest,
    user: dict = Depends(verify_token),
):
    logger.info("Meeting schedule requested", extra={"user_id": user.get("sub"), "meeting_type": request.meeting_type})

    task = schedule_meeting_task.delay(request.model_dump())

    await log_audit(
        action="schedule_meeting",
        entity_type="meeting",
        user_id=user.get("sub"),
        metadata={"meeting_type": request.meeting_type, "task_id": task.id},
    )

    return MeetingScheduleResponse(
        task_id=task.id,
        status="submitted",
        message="Meeting scheduling has been submitted. You will receive confirmation shortly.",
    )


@router.get("/types")
async def get_meeting_types():
    return {
        "meeting_types": [
            {"type": "google_meet", "label": "Google Meet", "description": "Video call via Google Meet"},
            {"type": "phone_call", "label": "Phone Call", "description": "Direct phone conversation"},
            {"type": "in_person", "label": "In Person", "description": "Face-to-face meeting (clients only)"},
        ]
    }
