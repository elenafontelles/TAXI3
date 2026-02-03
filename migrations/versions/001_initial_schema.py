"""Initial schema - all 10 tables

Revision ID: 001_initial
Revises: None
Create Date: 2026-02-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── owners ───────────────────────────────────────────────────────────
    op.create_table(
        "owners",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("tax_id", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tax_id", name="uq_owners_tax_id"),
    )

    # ── drivers ──────────────────────────────────────────────────────────
    op.create_table(
        "drivers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("license_number", sa.String(50), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("uber_driver_id", sa.String(100), nullable=True),
        sa.Column("freenow_driver_id", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"], name="fk_drivers_owner_id"),
        sa.UniqueConstraint("email", name="uq_drivers_email"),
        sa.UniqueConstraint("license_number", name="uq_drivers_license_number"),
    )

    # ── vehicles ─────────────────────────────────────────────────────────
    op.create_table(
        "vehicles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plate", sa.String(20), nullable=False),
        sa.Column("license_number", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("brand", sa.String(50), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("taximeter_id", sa.String(50), nullable=True),
        sa.Column("uber_vehicle_id", sa.String(100), nullable=True),
        sa.Column("freenow_vehicle_id", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"], name="fk_vehicles_owner_id"),
        sa.UniqueConstraint("plate", name="uq_vehicles_plate"),
    )

    # ── shifts ───────────────────────────────────────────────────────────
    op.create_table(
        "shifts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("driver_id", sa.String(36), nullable=False),
        sa.Column("vehicle_id", sa.String(36), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("km_free", sa.Numeric(10, 2), nullable=True),
        sa.Column("km_occupied", sa.Numeric(10, 2), nullable=True),
        sa.Column("max_speed", sa.Numeric(5, 1), nullable=True),
        sa.Column("total_earnings", sa.Numeric(10, 2), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], name="fk_shifts_driver_id"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], name="fk_shifts_vehicle_id"),
    )

    # ── trips ────────────────────────────────────────────────────────────
    op.create_table(
        "trips",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("driver_id", sa.String(36), nullable=False),
        sa.Column("vehicle_id", sa.String(36), nullable=False),
        sa.Column("shift_id", sa.String(36), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Numeric(10, 2), nullable=True),
        sa.Column("origin_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("origin_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("dest_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("dest_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("origin_address", sa.Text(), nullable=True),
        sa.Column("dest_address", sa.Text(), nullable=True),
        sa.Column("distance_km", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("gross_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("commission", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("platform_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("taxes_vat", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tips", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tolls", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("adjustments", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("payout_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("amount_breakdown", sa.JSON(), nullable=True),
        sa.Column("payment_method", sa.String(20), nullable=True),
        sa.Column("tariff_code", sa.String(20), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], name="fk_trips_driver_id"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], name="fk_trips_vehicle_id"),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.id"], name="fk_trips_shift_id"),
    )
    op.create_index("ix_trips_source", "trips", ["source"])
    op.create_index("ix_trips_external_id", "trips", ["external_id"])
    op.create_index("ix_trips_driver_id", "trips", ["driver_id"])
    op.create_index("ix_trips_vehicle_id", "trips", ["vehicle_id"])
    op.create_index("ix_trips_started_at", "trips", ["started_at"])

    # ── daily_summaries ──────────────────────────────────────────────────
    op.create_table(
        "daily_summaries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("driver_id", sa.String(36), nullable=True),
        sa.Column("vehicle_id", sa.String(36), nullable=True),
        sa.Column("trips_uber", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trips_freenow", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trips_prima", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trips_street", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_trips", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_km", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total_gross", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total_commission", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total_net", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("avg_trip_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("euro_per_km", sa.Numeric(10, 2), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], name="fk_daily_summaries_driver_id"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], name="fk_daily_summaries_vehicle_id"),
        sa.UniqueConstraint("date", "driver_id", "vehicle_id", name="uq_daily_summaries_date_driver_vehicle"),
    )

    # ── platform_tokens ──────────────────────────────────────────────────
    op.create_table(
        "platform_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("driver_id", sa.String(36), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(20), nullable=False, server_default="Bearer"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_refreshed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], name="fk_platform_tokens_driver_id"),
        sa.UniqueConstraint("driver_id", "platform", name="uq_platform_tokens_driver_platform"),
    )

    # ── sync_logs ────────────────────────────────────────────────────────
    op.create_table(
        "sync_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("sync_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("records_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Numeric(10, 2), nullable=True),
    )

    # ── freenow_imports ──────────────────────────────────────────────────
    op.create_table(
        "freenow_imports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("import_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("records_imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("file_hash", name="uq_freenow_imports_file_hash"),
    )

    # ── dsr_requests ─────────────────────────────────────────────────────
    op.create_table(
        "dsr_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("request_type", sa.String(20), nullable=False),
        sa.Column("subject_type", sa.String(20), nullable=False),
        sa.Column("subject_id", sa.String(36), nullable=False),
        sa.Column("requester_email", sa.String(255), nullable=False),
        sa.Column("verification_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("status", sa.String(20), nullable=False, server_default="received"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_data", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("dsr_requests")
    op.drop_table("freenow_imports")
    op.drop_table("sync_logs")
    op.drop_table("platform_tokens")
    op.drop_table("daily_summaries")
    op.drop_index("ix_trips_started_at", table_name="trips")
    op.drop_index("ix_trips_vehicle_id", table_name="trips")
    op.drop_index("ix_trips_driver_id", table_name="trips")
    op.drop_index("ix_trips_external_id", table_name="trips")
    op.drop_index("ix_trips_source", table_name="trips")
    op.drop_table("trips")
    op.drop_table("shifts")
    op.drop_table("vehicles")
    op.drop_table("drivers")
    op.drop_table("owners")
