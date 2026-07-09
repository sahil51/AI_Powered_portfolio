"""create memory tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-01

"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0002"
down_revision: str = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "memories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("conversation_id", sa.String(255), nullable=True, index=True),
        sa.Column("session_id", sa.String(255), nullable=True, index=True),
        sa.Column("key_namespace", sa.String(100), nullable=True),
        sa.Column("key_value", sa.String(255), nullable=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("memory_type", sa.String(50), nullable=False, server_default="fact"),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("scope", sa.String(50), nullable=False, index=True),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("confidence", sa.String(20), server_default="medium"),
        sa.Column("importance", sa.String(20), server_default="medium"),
        sa.Column("source", sa.String(50), server_default="system"),
        sa.Column("status", sa.String(20), nullable=False, index=True, server_default="active"),
        sa.Column("tags", sa.JSON, default=list),
        sa.Column("metadata", sa.JSON, default=dict),
        sa.Column("correlation_id", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_count", sa.BigInteger, server_default="0"),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean, default=False, index=True),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("user_id", "key_namespace", "key_value", name="uq_memory_user_key"),
    )

    op.create_table(
        "memory_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("memory_id", UUID(as_uuid=True), sa.ForeignKey("memories.id"), nullable=False, index=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("record_type", sa.String(50), server_default="snapshot"),
        sa.Column("tags", sa.JSON, default=list),
        sa.Column("metadata", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
    )

    op.create_table(
        "memory_tags",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("memory_id", UUID(as_uuid=True), sa.ForeignKey("memories.id"), nullable=False, index=True),
        sa.Column("tag", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.UniqueConstraint("memory_id", "tag", name="uq_memory_tag"),
    )

    op.create_table(
        "memory_audits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("memory_id", UUID(as_uuid=True), sa.ForeignKey("memories.id"), nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("previous_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("correlation_id", sa.String(255), nullable=True),
        sa.Column("metadata", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("memory_audits")
    op.drop_table("memory_tags")
    op.drop_table("memory_records")
    op.drop_table("memories")
