"""create knowledge document and chunk tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-01

"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0003"
down_revision: str = "0002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean, default=False, nullable=False, index=True),
        sa.Column("version", sa.Integer, server_default="1", nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("doc_type", sa.String(50), nullable=False, index=True),
        sa.Column("source_filename", sa.String(512), nullable=True),
        sa.Column("source_path", sa.Text, nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.BigInteger, server_default="0"),
        sa.Column("source_encoding", sa.String(20), server_default="utf-8"),
        sa.Column("source_metadata", sa.JSON, default=dict),
        sa.Column("status", sa.String(20), nullable=False, index=True),
        sa.Column("checksum", sa.String(64), server_default=""),
        sa.Column("correlation_id", sa.String(255), nullable=True, index=True),
        sa.Column("tags", sa.JSON, default=list),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column("doc_metadata_tags", sa.JSON, default=list),
        sa.Column("custom_metadata", sa.JSON, default=dict),
        sa.Column("max_chunk_size", sa.Integer, server_default="2000"),
        sa.Column("min_chunk_size", sa.Integer, server_default="100"),
        sa.Column("chunk_overlap", sa.Integer, server_default="200"),
        sa.Column("chunking_strategy", sa.String(30), server_default="fixed_size"),
        sa.Column("auto_activate", sa.Boolean, server_default="true"),
        sa.Column("enable_versioning", sa.Boolean, server_default="true"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean, default=False, nullable=False, index=True),
        sa.Column("version", sa.Integer, server_default="1", nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, server_default="0"),
        sa.Column("character_count", sa.Integer, server_default="0"),
        sa.Column("section", sa.String(255), nullable=True),
        sa.Column("heading", sa.String(512), nullable=True),
        sa.Column("chunk_metadata", sa.JSON, default=dict),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column("checksum", sa.String(64), server_default=""),
        sa.Column("embedding_status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("embedding", sa.JSON, nullable=True),
        sa.Column("embedding_dimension", sa.Integer, server_default="0"),
        sa.Column("embedding_model", sa.String(100), server_default=""),
        sa.Column("doc_version", sa.String(20), server_default="1.0.0"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_chunk_doc_index"),
    )

    op.create_index("idx_knowledge_docs_title", "knowledge_documents", ["title"],
                    postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_index("idx_knowledge_docs_type_status", "knowledge_documents", ["doc_type", "status"],
                    postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_index("idx_knowledge_docs_correlation", "knowledge_documents", ["correlation_id"],
                    postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_index("idx_knowledge_chunks_embed_status", "knowledge_chunks", ["embedding_status"],
                    postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_index("idx_knowledge_chunks_checksum", "knowledge_chunks", ["checksum"],
                    postgresql_where=sa.text("is_deleted = FALSE"))


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
