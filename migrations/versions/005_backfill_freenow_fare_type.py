"""Backfill FreeNow fare_type and payment_method from raw_data

Revision ID: 005_backfill_freenow
Revises: 004_settlement_redesign
Create Date: 2026-02-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "005_backfill_freenow"
down_revision = "004_settlement_redesign"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Backfill fare_type from raw_data for FreeNow trips
    # raw_data is JSON with key "FARE TYPE" containing "FIXED" or "METERED"
    conn.execute(sa.text(
        "UPDATE trips "
        "SET fare_type = UPPER(TRIM(raw_data->>'FARE TYPE')) "
        "WHERE source = 'freenow' "
        "AND fare_type IS NULL "
        "AND raw_data IS NOT NULL "
        "AND raw_data->>'FARE TYPE' IS NOT NULL "
        "AND UPPER(TRIM(raw_data->>'FARE TYPE')) IN ('FIXED', 'METERED')"
    ))

    # Backfill payment_method from old format to new
    # Old: "efectivo" -> "CASH", "tarjeta" -> "APP"
    conn.execute(sa.text(
        "UPDATE trips "
        "SET payment_method = 'CASH' "
        "WHERE source = 'freenow' "
        "AND payment_method = 'efectivo'"
    ))
    conn.execute(sa.text(
        "UPDATE trips "
        "SET payment_method = 'APP' "
        "WHERE source = 'freenow' "
        "AND payment_method = 'tarjeta'"
    ))


def downgrade() -> None:
    # Revert payment_method to old format
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE trips SET payment_method = 'efectivo' "
        "WHERE source = 'freenow' AND payment_method = 'CASH'"
    ))
    conn.execute(sa.text(
        "UPDATE trips SET payment_method = 'tarjeta' "
        "WHERE source = 'freenow' AND payment_method = 'APP'"
    ))
    # fare_type can stay as-is (it's correct data)
