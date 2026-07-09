from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from infrastructure.database.base import BaseEntity
from infrastructure.database.session import Base


class ConversationDBModel(BaseEntity, Base):
    __tablename__ = "conversations_v2"

    user_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    identity_source = Column(String(50), default="anonymous")
    state = Column(String(50), default="created", nullable=False, index=True)
    summary = Column(Text, nullable=True)
    correlation_id = Column(String(255), nullable=True)
    paused_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    source = Column(String(50), default="chat")
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    custom_fields = Column(JSON, default=dict)

    messages = relationship("MessageDBModel", back_populates="conversation", cascade="all, delete-orphan",
                            order_by="MessageDBModel.created_at")
    participants = relationship("ParticipantDBModel", back_populates="conversation", cascade="all, delete-orphan")


class MessageDBModel(BaseEntity, Base):
    __tablename__ = "conversation_messages"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations_v2.id"), nullable=False, index=True)
    message_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    participant_id = Column(String(255), nullable=True)
    correlation_id = Column(String(255), nullable=True)
    token_count = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, default=dict)
    attachments = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    conversation = relationship("ConversationDBModel", back_populates="messages")


class ParticipantDBModel(BaseEntity, Base):
    __tablename__ = "conversation_participants"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations_v2.id"), nullable=False, index=True)
    participant_id = Column(String(255), nullable=False)
    role = Column(String(50), default="participant")
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    left_at = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)

    conversation = relationship("ConversationDBModel", back_populates="participants")

    __table_args__ = (
        UniqueConstraint("conversation_id", "participant_id", name="uq_conversation_participant"),
    )
