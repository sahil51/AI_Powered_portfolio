from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from middleware.auth import verify_token
from monitoring.logger import logger
from tasks.notification_tasks import create_lead_task

router = APIRouter(prefix="/leads", tags=["Leads"])


class LeadCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    company: str = Field(..., min_length=1)
    phone: str | None = None
    notes: str | None = None


class LeadCreateResponse(BaseModel):
    task_id: str
    status: str
    message: str


@router.post("/create", response_model=LeadCreateResponse)
async def create_lead(request: LeadCreateRequest, user: dict = Depends(verify_token)):
    logger.info("Lead creation requested", extra={"email": request.email})
    task = create_lead_task.delay(request.model_dump())
    return LeadCreateResponse(
        task_id=task.id,
        status="submitted",
        message="Your information has been submitted. Sahil will get back to you soon.",
    )
