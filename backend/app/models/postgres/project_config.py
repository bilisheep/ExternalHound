"""
Project configuration ORM model.

Stores per-project database connection overrides.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class ProjectConfig(Base):
    """
    Project connection configuration.

    Keeps optional PostgreSQL and Neo4j connection overrides per project.
    """

    __tablename__ = "project_configs"
    __table_args__ = {"schema": "public", "comment": "Project connection config"}

    project_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="Project identifier",
    )

    postgres_host: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="PostgreSQL host",
    )
    postgres_port: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="PostgreSQL port",
    )
    postgres_user: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="PostgreSQL user",
    )
    postgres_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="PostgreSQL password",
    )
    postgres_db: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="PostgreSQL database",
    )
    postgres_sslmode: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="PostgreSQL SSL mode",
    )
    postgres_schema: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="PostgreSQL schema override",
    )

    neo4j_uri: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Neo4j URI",
    )
    neo4j_user: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Neo4j user",
    )
    neo4j_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Neo4j password",
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
