"""purge soft deleted records

Revision ID: 9f1a2b3c4d5e
Revises: 408a997e888f
Create Date: 2026-01-30 10:12:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "9f1a2b3c4d5e"
down_revision = "408a997e888f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM assets_relationship WHERE is_deleted = TRUE")
    op.execute("DELETE FROM assets_domain WHERE is_deleted = TRUE")
    op.execute("DELETE FROM assets_ip WHERE is_deleted = TRUE")
    op.execute("DELETE FROM assets_netblock WHERE is_deleted = TRUE")
    op.execute("DELETE FROM assets_organization WHERE is_deleted = TRUE")
    op.execute("DELETE FROM assets_service WHERE is_deleted = TRUE")
    op.execute("DELETE FROM assets_certificate WHERE is_deleted = TRUE")
    op.execute("DELETE FROM assets_client_application WHERE is_deleted = TRUE")
    op.execute("DELETE FROM assets_credential WHERE is_deleted = TRUE")


def downgrade() -> None:
    pass
