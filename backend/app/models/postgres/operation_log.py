"""
OperationLog ORM model.

Records audit events for changes to entities.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class OperationLog(Base):
    """Operation log model."""

    __tablename__ = "operation_logs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="UUID primary key",
    )
    operation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Operation type",
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Entity type",
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Entity identifier",
    )
    operation_detail: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Operation detail",
    )
    old_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Previous value",
    )
    new_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="New value",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Creation timestamp",
    )
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Creator identifier",
    )
    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
        comment="Client IP address",
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="User agent",
    )

    def __repr__(self) -> str:
        return f"<OperationLog(id={self.id}, entity_type={self.entity_type}, operation_type={self.operation_type})>"
