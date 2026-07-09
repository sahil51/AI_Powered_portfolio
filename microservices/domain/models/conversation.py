from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime = datetime.now(timezone.utc)
    metadata: dict = {}


class ConversationState(BaseModel):
    conversation_id: str
    user_id: str
    messages: list[Message] = []
    current_intent: Optional[str] = None
    pending_fields: dict = {}
    collected_data: dict = {}
    current_workflow: Optional[str] = None
    workflow_state: str = "idle"
    confirmation_pending: bool = False
    context: dict = {}
    summary: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
