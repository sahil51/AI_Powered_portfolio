from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel


class MeetingRequest(BaseModel):
    full_name: str
    email: str
    contact_number: str
    company_name: str
    company_address: str
    meeting_purpose: str
    preferred_date: str
    preferred_time: str
    timezone: str
    meeting_type: str
    location: Optional[str] = None
    additional_notes: Optional[str] = None


class MeetingSlot(BaseModel):
    date: str
    time: str
    timezone: str
    available: bool = True


class MeetingConfirmation(BaseModel):
    meeting_id: str
    details: MeetingRequest
    status: str = "pending"
    meet_link: Optional[str] = None
    calendar_event_id: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)
