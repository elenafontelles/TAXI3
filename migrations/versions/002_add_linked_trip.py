"""Add linked_trip_id to trips for cross-platform matching

Revision ID: 002_linked_trip
Revises: 001_initial
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_linked_trip"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add linked_trip_id column for cross-platform trip matching
    # Prima trips with 0 amount link to their FreeNow/Uber counterpart
    op.add_column(
        "trips",
        sa.Column("linked_trip_id", sa.String(36), nullable=True),
    )
    op.create_foreign_key(
        "fk_trips_linked_trip_id",
        "trips",
        "trips",
        ["linked_trip_id"],
        ["id"],
    )
    op.create_index("ix_trips_linked_trip_id", "trips", ["linked_trip_id"])


def downgrade() -> None:
    op.drop_index("ix_trips_linked_trip_id", table_name="trips")
    op.drop_constraint("fk_trips_linked_trip_id", "trips", type_="foreignkey")
    op.drop_column("trips", "linked_trip_id")
