from datetime import datetime, timezone

from sqlalchemy import JSON, BigInteger, Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from infrastructure.database.base import BaseEntity
from infrastructure.database.session import Base


class MemoryDBModel(BaseEntity, Base):
    __tablename__ = "memories"

    user_id = Column(String(255), nullable=False, index=True)
    conversation_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    key_namespace = Column(String(100), nullable=True)
    key_value = Column(String(255), nullable=True)
    value = Column(Text, nullable=False)
    memory_type = Column(String(50), default="fact", nullable=False)
    category = Column(String(50), nullable=False, index=True)
    scope = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), default="medium")
    confidence = Column(String(20), default="medium")
    importance = Column(String(20), default="medium")
    source = Column(String(50), default="system")
    status = Column(String(20), default="active", nullable=False, index=True)
    tags = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)
    correlation_id = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(BigInteger, default=0)
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    records = relationship("MemoryRecordDBModel", back_populates="memory", cascade="all, delete-orphan",
                           order_by="MemoryRecordDBModel.created_at")
    tags_list = relationship("MemoryTagModel", back_populates="memory", cascade="all, delete-orphan")
    audits = relationship("MemoryAuditModel", back_populates="memory", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "key_namespace", "key_value", name="uq_memory_user_key"),
        {"extend_existing": True},
    )


class MemoryRecordDBModel(BaseEntity, Base):
    __tablename__ = "memory_records"

    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id"), nullable=False, index=True)
    value = Column(Text, nullable=False)
    record_type = Column(String(50), default="snapshot")
    tags = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)

    memory = relationship("MemoryDBModel", back_populates="records")


class MemoryTagModel(BaseEntity, Base):
    __tablename__ = "memory_tags"

    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id"), nullable=False, index=True)
    tag = Column(String(100), nullable=False)

    memory = relationship("MemoryDBModel", back_populates="tags_list")

    __table_args__ = (
        UniqueConstraint("memory_id", "tag", name="uq_memory_tag"),
    )


class MemoryAuditModel(BaseEntity, Base):
    __tablename__ = "memory_audits"

    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    previous_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    user_id = Column(String(255), nullable=True)
    correlation_id = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)

    memory = relationship("MemoryDBModel", back_populates="audits")
