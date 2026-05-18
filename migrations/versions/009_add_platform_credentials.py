"""Add platform_credentials table

Revision ID: 009_platform_creds
Revises: 008_freenow_adj
Create Date: 2026-05-18

"""
from alembic import op
import sqlalchemy as sa

revision = "009_platform_creds"
down_revision = "008_freenow_adj"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("account_label", sa.String(50), nullable=False, server_default=""),
        sa.Column("email", sa.String(255), nullable=False, server_default=""),
        sa.Column("encrypted_password", sa.Text(), nullable=False, server_default=""),
        sa.Column("extra_config", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )
    op.create_index(
        "ix_platform_creds_platform_label",
        "platform_credentials",
        ["platform", "account_label"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_platform_creds_platform_label", table_name="platform_credentials")
    op.drop_table("platform_credentials")
