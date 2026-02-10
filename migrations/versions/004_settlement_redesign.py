"""Settlement redesign: rename commission fields, add new tables

Revision ID: 004_settlement_redesign
Revises: 003_settlement
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "004_settlement_redesign"
down_revision = "003_settlement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Rename commission fields in drivers ─────────────────────────────
    op.alter_column("drivers", "commission_base_pct", new_column_name="prima_base_pct")
    op.alter_column("drivers", "commission_bonus_pct", new_column_name="prima_bonus_pct")

    # ── Add fuel_deducted_from_driver to drivers ────────────────────────
    op.add_column(
        "drivers",
        sa.Column("fuel_deducted_from_driver", sa.Boolean(), nullable=False, server_default="false"),
    )

    # ── Add fare_type to trips ──────────────────────────────────────────
    op.add_column(
        "trips",
        sa.Column("fare_type", sa.String(20), nullable=True),
    )

    # ── tpv_daily_totals ───────────────────────────────────────────────
    op.create_table(
        "tpv_daily_totals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("vehicle_id", sa.String(36), nullable=False),
        sa.Column("license_number", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("source_file", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], name="fk_tpv_daily_totals_vehicle_id"),
    )
    op.create_index("ix_tpv_daily_totals_date", "tpv_daily_totals", ["date"])
    op.create_index("ix_tpv_daily_totals_vehicle_id", "tpv_daily_totals", ["vehicle_id"])

    # ── uber_daily_summaries ───────────────────────────────────────────
    op.create_table(
        "uber_daily_summaries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("license_number", sa.String(50), nullable=False),
        sa.Column("vehicle_id", sa.String(36), nullable=True),
        sa.Column("total_earnings", sa.Numeric(10, 2), nullable=True),
        sa.Column("taximeter", sa.Numeric(10, 2), nullable=True),
        sa.Column("refund", sa.Numeric(10, 2), nullable=True),
        sa.Column("adjustments", sa.Numeric(10, 2), nullable=True),
        sa.Column("t3_fixed", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_payment", sa.Numeric(10, 2), nullable=False),
        sa.Column("source_file", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], name="fk_uber_daily_summaries_vehicle_id"),
    )
    op.create_index("ix_uber_daily_summaries_date", "uber_daily_summaries", ["date"])
    op.create_index("ix_uber_daily_summaries_license_number", "uber_daily_summaries", ["license_number"])


def downgrade() -> None:
    # Drop new tables
    op.drop_index("ix_uber_daily_summaries_license_number", table_name="uber_daily_summaries")
    op.drop_index("ix_uber_daily_summaries_date", table_name="uber_daily_summaries")
    op.drop_table("uber_daily_summaries")

    op.drop_index("ix_tpv_daily_totals_vehicle_id", table_name="tpv_daily_totals")
    op.drop_index("ix_tpv_daily_totals_date", table_name="tpv_daily_totals")
    op.drop_table("tpv_daily_totals")

    # Remove new columns
    op.drop_column("trips", "fare_type")
    op.drop_column("drivers", "fuel_deducted_from_driver")

    # Rename back
    op.alter_column("drivers", "prima_bonus_pct", new_column_name="commission_bonus_pct")
    op.alter_column("drivers", "prima_base_pct", new_column_name="commission_base_pct")
