"""Parse Prima/Taxitronic CSV export into normalized shift dicts."""
import csv
from datetime import datetime


def parse_prima_csv(filepath: str) -> list[dict]:
    """Parse Prima/Taxitronic shift-level CSV export into normalized shift dicts.

    Expected columns: Shift ID, Date, Start Time, End Time,
                      KM Free, KM Occupied, Trips, Total EUR

    Note: Prima data is shift-level, not trip-level. Each row represents
    an entire shift with aggregated metrics.

    Returns a list of dicts ready for Shift model creation.
    """
    shifts = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row["Date"].strip()
            start_time_str = row["Start Time"].strip()
            end_time_str = row["End Time"].strip()

            started_at = datetime.strptime(
                f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M"
            )
            ended_at = datetime.strptime(
                f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M"
            )

            shifts.append({
                "source": "prima",
                "external_id": row["Shift ID"].strip(),
                "started_at": started_at,
                "ended_at": ended_at,
                "km_free": float(row["KM Free"].strip()),
                "km_occupied": float(row["KM Occupied"].strip()),
                "total_earnings": float(row["Total EUR"].strip()),
                "raw_data": dict(row),
            })
    return shifts
