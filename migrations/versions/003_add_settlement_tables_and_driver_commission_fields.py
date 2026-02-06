"""Add settlement tables and driver commission fields

Revision ID: 003_settlement
Revises: 002_linked_trip
Create Date: 2026-02-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003_settlement"
down_revision = "002_linked_trip"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Add commission fields to drivers ──────────────────────────────────
    op.add_column(
        "drivers",
        sa.Column("commission_base_pct", sa.Numeric(5, 2), nullable=False, server_default="40.0"),
    )
    op.add_column(
        "drivers",
        sa.Column("commission_bonus_pct", sa.Numeric(5, 2), nullable=False, server_default="45.0"),
    )
    op.add_column(
        "drivers",
        sa.Column("commission_threshold", sa.Numeric(10, 2), nullable=False, server_default="300.0"),
    )
    op.add_column(
        "drivers",
        sa.Column("freenow_commission_driver_pct", sa.Numeric(5, 2), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "drivers",
        sa.Column("uber_commission_driver_pct", sa.Numeric(5, 2), nullable=False, server_default="0.0"),
    )

    # ── pending_validations ───────────────────────────────────────────────
    op.create_table(
        "pending_validations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("trip_id", sa.String(36), nullable=True),
        sa.Column("validation_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], name="fk_pending_validations_trip_id"),
    )
    op.create_index("ix_pending_validations_status", "pending_validations", ["status"])
    op.create_index("ix_pending_validations_validation_type", "pending_validations", ["validation_type"])

    # ── visa_payments ─────────────────────────────────────────────────────
    op.create_table(
        "visa_payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column("terminal_id", sa.String(50), nullable=False),
        sa.Column("card_last4", sa.String(20), nullable=False),
        sa.Column("brand", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("trip_id", sa.String(36), nullable=True),
        sa.Column("tip_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("source_file", sa.String(255), nullable=False),
        sa.Column("vehicle_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], name="fk_visa_payments_trip_id"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], name="fk_visa_payments_vehicle_id"),
    )
    op.create_index("ix_visa_payments_date", "visa_payments", ["date"])
    op.create_index("ix_visa_payments_vehicle_id", "visa_payments", ["vehicle_id"])
    op.create_index("ix_visa_payments_trip_id", "visa_payments", ["trip_id"])

    # ── fuel_expenses ─────────────────────────────────────────────────────
    op.create_table(
        "fuel_expenses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("vehicle_id", sa.String(36), nullable=False),
        sa.Column("driver_id", sa.String(36), nullable=True),
        sa.Column("liters", sa.Numeric(10, 2), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("source_file", sa.String(255), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], name="fk_fuel_expenses_vehicle_id"),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], name="fk_fuel_expenses_driver_id"),
    )
    op.create_index("ix_fuel_expenses_date", "fuel_expenses", ["date"])
    op.create_index("ix_fuel_expenses_vehicle_id", "fuel_expenses", ["vehicle_id"])
    op.create_index("ix_fuel_expenses_driver_id", "fuel_expenses", ["driver_id"])

    # ── other_expenses ────────────────────────────────────────────────────
    op.create_table(
        "other_expenses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("driver_id", sa.String(36), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], name="fk_other_expenses_driver_id"),
    )
    op.create_index("ix_other_expenses_date", "other_expenses", ["date"])
    op.create_index("ix_other_expenses_driver_id", "other_expenses", ["driver_id"])
    op.create_index("ix_other_expenses_category", "other_expenses", ["category"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index("ix_other_expenses_category", table_name="other_expenses")
    op.drop_index("ix_other_expenses_driver_id", table_name="other_expenses")
    op.drop_index("ix_other_expenses_date", table_name="other_expenses")
    op.drop_table("other_expenses")

    op.drop_index("ix_fuel_expenses_driver_id", table_name="fuel_expenses")
    op.drop_index("ix_fuel_expenses_vehicle_id", table_name="fuel_expenses")
    op.drop_index("ix_fuel_expenses_date", table_name="fuel_expenses")
    op.drop_table("fuel_expenses")

    op.drop_index("ix_visa_payments_trip_id", table_name="visa_payments")
    op.drop_index("ix_visa_payments_vehicle_id", table_name="visa_payments")
    op.drop_index("ix_visa_payments_date", table_name="visa_payments")
    op.drop_table("visa_payments")

    op.drop_index("ix_pending_validations_validation_type", table_name="pending_validations")
    op.drop_index("ix_pending_validations_status", table_name="pending_validations")
    op.drop_table("pending_validations")

    # Remove commission fields from drivers
    op.drop_column("drivers", "uber_commission_driver_pct")
    op.drop_column("drivers", "freenow_commission_driver_pct")
    op.drop_column("drivers", "commission_threshold")
    op.drop_column("drivers", "commission_bonus_pct")
    op.drop_column("drivers", "commission_base_pct")
