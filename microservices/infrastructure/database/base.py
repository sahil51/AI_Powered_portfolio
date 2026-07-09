import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID


class TimeStampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    def soft_delete(self) -> None:
        self.is_deleted = True  # type: ignore[assignment]

    def restore(self) -> None:
        self.is_deleted = False  # type: ignore[assignment]


class VersionMixin:
    version = Column(Integer, default=1, nullable=False)

    def increment_version(self) -> None:
        self.version += 1  # type: ignore[assignment]


class AuditMixin:
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)


class BaseEntity(TimeStampMixin, SoftDeleteMixin, VersionMixin, AuditMixin):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    __mapper_args__ = {"version_id_col": "version"}
