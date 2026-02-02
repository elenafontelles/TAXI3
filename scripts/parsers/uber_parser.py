"""Parse Uber driver CSV export into normalized trip dicts."""
import csv
from datetime import datetime


def parse_uber_csv(filepath: str) -> list[dict]:
    """Parse Uber driver CSV export into normalized trip dicts.

    Expected columns: Trip ID, Driver, Date/Time, City, Product,
                      Fare, Tip, Tolls, Total

    Returns a list of dicts ready for Trip model creation.
    """
    trips = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trips.append({
                "source": "uber",
                "external_id": row["Trip ID"].strip(),
                "started_at": datetime.strptime(
                    row["Date/Time"].strip(), "%Y-%m-%d %H:%M"
                ),
                "gross_amount": float(row["Total"].strip()),
                "commission": float(row["Total"].strip()) - float(row["Fare"].strip()),
                "tips": float(row["Tip"].strip()),
                "tolls": float(row["Tolls"].strip()),
                "payout_amount": float(row["Fare"].strip()),
                "payment_method": "card",
                "raw_data": dict(row),
            })
    return trips
