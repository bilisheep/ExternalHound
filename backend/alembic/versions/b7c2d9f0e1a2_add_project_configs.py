"""add_project_configs

Revision ID: b7c2d9f0e1a2
Revises: 9f1a2b3c4d5e
Create Date: 2026-02-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7c2d9f0e1a2"
down_revision = "9f1a2b3c4d5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_configs",
        sa.Column("project_id", sa.String(length=64), nullable=False, comment="Project identifier"),
        sa.Column("postgres_host", sa.String(length=255), nullable=True, comment="PostgreSQL host"),
        sa.Column("postgres_port", sa.Integer(), nullable=True, comment="PostgreSQL port"),
        sa.Column("postgres_user", sa.String(length=255), nullable=True, comment="PostgreSQL user"),
        sa.Column("postgres_password", sa.String(length=255), nullable=True, comment="PostgreSQL password"),
        sa.Column("postgres_db", sa.String(length=255), nullable=True, comment="PostgreSQL database"),
        sa.Column("postgres_sslmode", sa.String(length=20), nullable=True, comment="PostgreSQL SSL mode"),
        sa.Column("postgres_schema", sa.String(length=64), nullable=True, comment="PostgreSQL schema override"),
        sa.Column("neo4j_uri", sa.String(length=255), nullable=True, comment="Neo4j URI"),
        sa.Column("neo4j_user", sa.String(length=255), nullable=True, comment="Neo4j user"),
        sa.Column("neo4j_password", sa.String(length=255), nullable=True, comment="Neo4j password"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Update timestamp",
        ),
        sa.PrimaryKeyConstraint("project_id", name=op.f("pk_project_configs")),
        schema="public",
        comment="Project connection config",
    )


def downgrade() -> None:
    op.drop_table("project_configs", schema="public")
