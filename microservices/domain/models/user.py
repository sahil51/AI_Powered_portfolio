from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    id: str = ""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    company_address: Optional[str] = None
    preferred_language: str = "en"
    preferred_meeting_type: Optional[str] = None
    preferred_time: Optional[str] = None
    preferred_timezone: Optional[str] = None
    user_type: str = "visitor"
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
