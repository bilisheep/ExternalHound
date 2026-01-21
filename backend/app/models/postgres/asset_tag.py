"""
AssetTag ORM model.

Associates tags with assets.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class AssetTag(Base):
    """Asset-tag association model."""

    __tablename__ = "asset_tags"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="UUID primary key",
    )
    asset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Asset type",
    )
    asset_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Asset identifier",
    )
    tag_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        comment="Tag identifier",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Creation timestamp",
    )
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Creator identifier",
    )

    __table_args__ = (
        UniqueConstraint(
            "asset_type",
            "asset_id",
            "tag_id",
            name="uq_asset_tag",
        ),
        Index("ix_asset_tags_asset_type_asset_id", "asset_type", "asset_id"),
        Index("ix_asset_tags_tag_id", "tag_id"),
        Index("ix_asset_tags_created_at", "created_at"),
        {"comment": "Asset tags"},
    )

    def __repr__(self) -> str:
        return f"<AssetTag(id={self.id}, asset_type={self.asset_type}, asset_id={self.asset_id})>"
