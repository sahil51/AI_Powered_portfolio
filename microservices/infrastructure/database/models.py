from sqlalchemy import JSON, Column, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from infrastructure.database.base import BaseEntity
from infrastructure.database.session import Base


class UserModel(BaseEntity, Base):
    __tablename__ = "users"

    session_id = Column(String(255), nullable=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    company_address = Column(Text, nullable=True)
    preferred_language = Column(String(10), default="en")
    preferred_meeting_type = Column(String(50), nullable=True)
    preferred_time = Column(String(50), nullable=True)
    preferred_timezone = Column(String(50), nullable=True)
    user_type = Column(String(50), default="visitor")

    conversations = relationship("ConversationModel", back_populates="user")
    meetings = relationship("MeetingModel", back_populates="user")


class ConversationModel(BaseEntity, Base):
    __tablename__ = "conversations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    messages = Column(JSON, default=list)
    current_intent = Column(String(100), nullable=True)
    current_workflow = Column(String(100), nullable=True)
    workflow_state = Column(String(50), default="idle")
    context = Column(JSON, default=dict)
    summary = Column(Text, nullable=True)

    user = relationship("UserModel", back_populates="conversations")


class MeetingModel(BaseEntity, Base):
    __tablename__ = "meetings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    meeting_type = Column(String(50), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    contact_number = Column(String(50), nullable=False)
    company_name = Column(String(255), nullable=False)
    company_address = Column(Text, nullable=False)
    meeting_purpose = Column(Text, nullable=False)
    preferred_date = Column(String(50), nullable=False)
    preferred_time = Column(String(50), nullable=False)
    timezone = Column(String(50), nullable=False)
    location = Column(Text, nullable=True)
    meet_link = Column(Text, nullable=True)
    calendar_event_id = Column(String(255), nullable=True)
    status = Column(String(50), default="scheduled")

    user = relationship("UserModel", back_populates="meetings")


class LeadModel(BaseEntity, Base):
    __tablename__ = "leads"

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    source = Column(String(100), default="chat")
    status = Column(String(50), default="new")
    score = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)


class AuditLogModel(BaseEntity, Base):
    __tablename__ = "audit_logs"

    action = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)
    conversation_id = Column(String(255), nullable=True)
    meta_data = Column("metadata", JSON, default=dict)
