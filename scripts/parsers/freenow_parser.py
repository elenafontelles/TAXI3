"""Parse FreeNow driver CSV export into normalized trip dicts."""
import csv
from datetime import datetime


def parse_freenow_csv(filepath: str) -> list[dict]:
    """Parse FreeNow driver CSV export into normalized trip dicts.

    Expected columns: Booking ID, Date, Time, Pickup, Dropoff,
                      Distance (km), Duration (min), Fare (EUR),
                      Commission (EUR), Net (EUR)

    Returns a list of dicts ready for Trip model creation.
    """
    trips = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row["Date"].strip()
            time_str = row["Time"].strip()
            started_at = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

            trips.append({
                "source": "freenow",
                "external_id": row["Booking ID"].strip(),
                "started_at": started_at,
                "gross_amount": float(row["Fare (EUR)"].strip()),
                "commission": float(row["Commission (EUR)"].strip()),
                "payout_amount": float(row["Net (EUR)"].strip()),
                "distance_km": float(row["Distance (km)"].strip()),
                "duration_minutes": float(row["Duration (min)"].strip()),
                "origin_address": row["Pickup"].strip(),
                "dest_address": row["Dropoff"].strip(),
                "payment_method": "card",
                "raw_data": dict(row),
            })
    return trips
