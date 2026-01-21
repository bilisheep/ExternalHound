"""
Tag ORM model.

Represents tags for classifying assets.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Tag(Base):
    """Tag model."""

    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="UUID primary key",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Tag name",
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Tag category",
    )
    color: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Display color",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description",
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Usage count",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
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
        comment="Creator identifier",
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"
