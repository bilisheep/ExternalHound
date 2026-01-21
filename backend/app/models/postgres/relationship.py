"""
Relationship ORM model.

Stores asset relationships as edges in PostgreSQL, providing a persistent
record of graph relationships that are also synced to Neo4j.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Relationship(Base):
    """
    Asset relationship edge model.

    Represents a directed edge between two assets in the graph. Each relationship
    has a unique combination of source, target, type, and edge_key to support
    multiple relationships of the same type between the same nodes.
    """

    __tablename__ = "assets_relationship"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="UUID primary key",
    )

    # Source node
    source_external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Source node external id",
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Source node type (e.g., Organization, Domain, IP)",
    )

    # Target node
    target_external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Target node external id",
    )
    target_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Target node type (e.g., Organization, Domain, IP)",
    )

    # Relationship metadata
    relation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Relationship type (e.g., OWNS_DOMAIN, RESOLVES_TO)",
    )
    edge_key: Mapped[str] = mapped_column(
        String(255),
        default="default",
        nullable=False,
        comment="Disambiguation key for multiple edges of same type",
    )
    properties: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Relationship properties (e.g., percent, record_type, first_seen)",
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Soft delete flag",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Deletion timestamp",
    )

    # Audit fields
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
        comment="Last update timestamp",
    )
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Creator identifier",
    )

    __table_args__ = (
        UniqueConstraint(
            "source_external_id",
            "source_type",
            "target_external_id",
            "target_type",
            "relation_type",
            "edge_key",
            name="uq_assets_relationship_key",
        ),
        {"comment": "Asset relationships (edges in the graph)"},
    )

    def __repr__(self) -> str:
        """Return string representation of the relationship."""
        return (
            f"<Relationship(id={self.id}, "
            f"type={self.relation_type}, "
            f"source={self.source_type}:{self.source_external_id}, "
            f"target={self.target_type}:{self.target_external_id})>"
        )
