from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from infrastructure.database.base import BaseEntity
from infrastructure.database.session import Base


class DocumentDBModel(BaseEntity, Base):
    __tablename__ = "knowledge_documents"

    title = Column(String(512), nullable=True)
    doc_type = Column(String(50), nullable=False, index=True)
    source_filename = Column(String(512), nullable=True)
    source_path = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(BigInteger, default=0)
    source_encoding = Column(String(20), default="utf-8")
    source_metadata = Column(JSON, default=dict)
    status = Column(String(20), nullable=False, index=True)
    checksum = Column(String(64), default="")
    correlation_id = Column(String(255), nullable=True, index=True)
    tags = Column(JSON, default=list)

    author = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    content_type = Column(String(100), nullable=True)
    language = Column(String(10), default="en")
    doc_metadata_tags = Column(JSON, default=list)
    custom_metadata = Column(JSON, default=dict)

    max_chunk_size = Column(Integer, default=2000)
    min_chunk_size = Column(Integer, default=100)
    chunk_overlap = Column(Integer, default=200)
    chunking_strategy = Column(String(30), default="fixed_size")
    auto_activate = Column(Boolean, default=True)
    enable_versioning = Column(Boolean, default=True)

    processed_at = Column(DateTime(timezone=True), nullable=True)
    embedded_at = Column(DateTime(timezone=True), nullable=True)
    indexed_at = Column(DateTime(timezone=True), nullable=True)

    chunks = relationship(
        "ChunkDBModel",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="ChunkDBModel.chunk_index",
    )

    __table_args__ = {"extend_existing": True}


class ChunkDBModel(BaseEntity, Base):
    __tablename__ = "knowledge_chunks"

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    section = Column(String(255), nullable=True)
    heading = Column(String(512), nullable=True)
    chunk_metadata = Column(JSON, default=dict)
    language = Column(String(10), default="en")
    checksum = Column(String(64), default="")
    embedding_status = Column(String(20), nullable=False, default="pending", index=True)
    embedding = Column(JSON, nullable=True)
    embedding_dimension = Column(Integer, default=0)
    embedding_model = Column(String(100), default="")
    doc_version = Column(String(20), default="1.0.0")

    document = relationship("DocumentDBModel", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk_doc_index"),
        {"extend_existing": True},
    )
