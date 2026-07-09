from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class LeadCreatedEvent:
    lead_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    email: str = ""
    company: str = ""
    source: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LeadQualifiedEvent:
    lead_id: str = ""
    qualified_by: str = ""
    qualification_score: float = 0.0
    qualified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
