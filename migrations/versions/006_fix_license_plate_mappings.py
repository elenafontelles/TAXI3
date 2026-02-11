"""Fix driver license_number and vehicle plate mappings

Correct mappings:
  361 - 0397MSS
  092 - 8921LYW
  1061 - 2965MMM

Revision ID: 006_fix_license_plate
Revises: 005_backfill_freenow
Create Date: 2026-02-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "006_fix_license_plate"
down_revision = "005_backfill_freenow"
branch_labels = None
depends_on = None

# Correct mappings: license_number_prefix -> plate
CORRECT_MAPPINGS = {
    "361": "0397MSS",
    "092": "8921LYW",
    "1061": "2965MMM",
}


def upgrade() -> None:
    conn = op.get_bind()

    for lic_num, plate in CORRECT_MAPPINGS.items():
        correct_value = f"{lic_num} - {plate}"

        # Update drivers: any driver whose license_number starts with this prefix
        conn.execute(sa.text(
            "UPDATE drivers "
            "SET license_number = :correct "
            "WHERE license_number LIKE :pattern "
            "AND license_number != :correct"
        ), {"correct": correct_value, "pattern": f"{lic_num} - %"})

        # Also handle drivers with just the number (no plate)
        conn.execute(sa.text(
            "UPDATE drivers "
            "SET license_number = :correct "
            "WHERE TRIM(license_number) = :lic_num"
        ), {"correct": correct_value, "lic_num": lic_num})

        # Update vehicles: fix plate for vehicles with this license_number
        conn.execute(sa.text(
            "UPDATE vehicles "
            "SET plate = :plate "
            "WHERE TRIM(LEADING '0' FROM license_number) = TRIM(LEADING '0' FROM :lic_num)"
        ), {"plate": plate, "lic_num": lic_num})


def downgrade() -> None:
    # Data migration - no automatic downgrade
    pass
