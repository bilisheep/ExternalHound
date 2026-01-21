"""
ImportLog ORM model.

Tracks dataset import jobs and their outcomes.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class ImportLog(Base):
    """Import log model."""

    __tablename__ = "import_logs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="UUID primary key",
    )
    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Source file name",
    )
    file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="File size in bytes",
    )
    file_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="File hash",
    )
    file_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Stored file path",
    )
    format: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="File format",
    )
    parser_version: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Parser version",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Import status",
    )
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Progress percentage",
    )
    records_total: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total records",
    )
    records_success: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Successful records",
    )
    records_failed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Failed records",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error summary",
    )
    error_details: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Error details",
    )
    assets_created: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Created assets summary",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Update timestamp",
    )
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Creator identifier",
    )
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Duration in seconds",
    )

    def __repr__(self) -> str:
        return f"<ImportLog(id={self.id}, filename={self.filename}, status={self.status})>"
