"""Parse FreeNow driver CSV export into normalized trip dicts."""
import csv
from datetime import datetime


def parse_freenow_csv(filepath: str) -> list[dict]:
    """Parse FreeNow booking record CSV export.

    Real format: comma-separated, ISO 8601 dates with timezone,
    dot decimals. Only imports ACCOMPLISHED bookings.

    Returns a list of dicts ready for Trip model creation.
    """
    trips = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["BOOKING STATE"].strip() != "ACCOMPLISHED":
                continue

            gross = float(row["TOUR VALUE"].strip())
            tips = float(row["TOUR TIP"].strip())
            tolls = float(row["TOLL VALUE"].strip())
            tax_pct = float(row["TAX PERCENTAGE"].strip())

            started_at = datetime.fromisoformat(row["PICKUP DATE"].strip())
            ended_at = datetime.fromisoformat(row["CLOSED DATE"].strip())
            duration = (ended_at - started_at).total_seconds() / 60

            payment_raw = row["PAYMENT METHOD"].strip().upper()
            payment = "CASH" if payment_raw == "CASH" else "APP"

            fare_type_raw = row.get("FARE TYPE", "").strip().upper()
            fare_type = fare_type_raw if fare_type_raw in ("FIXED", "METERED") else None

            trips.append({
                "source": "freenow",
                "external_id": row["BOOKING ID"].strip(),
                "started_at": started_at,
                "ended_at": ended_at,
                "duration_minutes": round(duration, 2),
                "gross_amount": gross,
                "commission": 0,
                "taxes_vat": round(gross * tax_pct / 100, 2) if tax_pct else 0,
                "tips": tips,
                "tolls": tolls,
                "payout_amount": gross,
                "payment_method": payment,
                "fare_type": fare_type,
                "origin_address": row["PICKUP LOCATION"].strip() or None,
                "dest_address": row["DROPOFF LOCATION"].strip() or None,
                "raw_data": dict(row),
                "_driver_name": f"{row['DRIVER FIRST NAME'].strip()} {row['DRIVER LAST NAME'].strip()}",
                "_plate": row["LICENCE PLATE"].strip(),
            })
    return trips
