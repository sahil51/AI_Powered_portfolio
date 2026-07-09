from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel


class Lead(BaseModel):
    id: str = ""
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    source: str = "chat"
    status: str = "new"
    score: float = 0.0
    notes: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
