"""Add km_free column to trips table

Revision ID: 007_add_km_free
Revises: 006_fix_license_plate
Create Date: 2026-02-20

"""
from alembic import op
import sqlalchemy as sa


revision = "007_add_km_free"
down_revision = "006_fix_license_plate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("km_free", sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("trips", "km_free")
