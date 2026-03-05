"""Add freenow_adjustments table

Revision ID: 008_freenow_adj
Revises: 007_add_km_free
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa

revision = "008_freenow_adj"
down_revision = "007_add_km_free"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "freenow_adjustments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("driver_id", sa.String(36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("adjustment_type", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_freenow_adj_driver_date", "freenow_adjustments", ["driver_id", "date"])


def downgrade() -> None:
    op.drop_index("ix_freenow_adj_driver_date", table_name="freenow_adjustments")
    op.drop_table("freenow_adjustments")
