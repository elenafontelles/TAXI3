"""Parse Prima/Taxitronic CSV export into normalized trip dicts."""
import csv
from datetime import datetime


def _parse_decimal(value: str) -> float:
    """Parse European decimal format (comma as separator)."""
    value = value.strip()
    if not value:
        return 0.0
    return float(value.replace(",", "."))


def _parse_coord(value: str) -> float | None:
    """Parse coordinate like '41.213100N' or '2.056400E'."""
    value = value.strip()
    if not value:
        return None
    direction = value[-1]
    num = float(value[:-1])
    if direction in ("S", "W"):
        num = -num
    return num


def parse_prima_csv(filepath: str) -> list[dict]:
    """Parse Prima/Taxitronic trip-level CSV export.

    Real format: semicolon-separated, European decimals (comma),
    dates as d/m/yy H:MM, coordinates as '41.213100N'.

    Returns a list of dicts ready for Trip model creation.
    """
    trips = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            gross = _parse_decimal(row["AmountTotalPaid"])

            started_at = datetime.strptime(
                row["DateTripStart"].strip(), "%d/%m/%y %H:%M"
            )
            ended_at = datetime.strptime(
                row["DateTripEnd"].strip(), "%d/%m/%y %H:%M"
            )

            duration = (ended_at - started_at).total_seconds() / 60

            trips.append({
                "source": "prima",
                "external_id": row["TripNumber"].strip(),
                "started_at": started_at,
                "ended_at": ended_at,
                "duration_minutes": round(duration, 2),
                "gross_amount": gross,
                "commission": 0,
                "tips": _parse_decimal(row["AmountTips"]),
                "tolls": _parse_decimal(row["AmountTolls"]),
                "payout_amount": gross,
                "payment_method": row["PaymentMode"].strip().lower(),
                "distance_km": _parse_decimal(row["km"]),
                "tariff_code": row["TariffsUsed"].strip(),
                "origin_lat": _parse_coord(row.get("TripStartLatitude", "")),
                "origin_lng": _parse_coord(row.get("TripStartLongitude", "")),
                "dest_lat": _parse_coord(row.get("TripEndLatitude", "")),
                "dest_lng": _parse_coord(row.get("TripEndLongitude", "")),
                "origin_address": " ".join(filter(None, [
                    row.get("StartStreet", "").strip(),
                    row.get("StartStreetNum", "").strip(),
                    row.get("StartCity", "").strip(),
                ])) or None,
                "dest_address": " ".join(filter(None, [
                    row.get("EndStreet", "").strip(),
                    row.get("EndStreetNum", "").strip(),
                    row.get("EndCity", "").strip(),
                ])) or None,
                "raw_data": dict(row),
            })
    return trips
