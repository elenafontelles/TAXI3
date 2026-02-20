"""Parse Prima/Taxitronic CSV export into normalized trip dicts."""
import csv
from datetime import datetime


def _parse_decimal(value: str) -> float:
    """Parse European decimal format (comma as separator)."""
    value = value.strip()
    if not value:
        return 0.0
    return float(value.replace(",", "."))


def _parse_time_to_minutes(value: str) -> float:
    """Parse HH:MM:SS time string to minutes.

    Examples: '0:00:18' → 0.3, '0:12:30' → 12.5, '1:05:00' → 65.0
    """
    value = value.strip()
    if not value:
        return 0.0
    parts = value.split(":")
    if len(parts) == 3:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        return round((h * 3600 + m * 60 + s) / 60, 2)
    return 0.0


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


def _parse_datetime(value: str) -> datetime:
    """Parse Prima datetime — handles both real and legacy formats.

    Real export: '02/02/2026 1:19:03' (%d/%m/%Y %H:%M:%S, no leading-zero hour)
    Legacy:      '27/01/26 9:00'      (%d/%m/%y %H:%M)
    """
    value = value.strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%y %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse Prima datetime: {value!r}")


# Taxitronic uses generic codes ("CONDCUTOR 1") instead of real names.
# Map DriverNum → real driver name for matching against the DB.
_CONDUCTOR_MAP = {
    "1": "TAMARA ROSA GOMEZ",
    "3": "SALVADOR CARMONA CARMONA",
    "4": "IVAN ALSINA BURGOS",
}


def parse_prima_csv(filepath: str) -> list[dict]:
    """Parse Prima/Taxitronic trip-level CSV export.

    Real format: semicolon-separated, European decimals (comma),
    dates as d/m/Y H:MM:SS, coordinates as '41.213100N'.

    Returns a list of dicts ready for Trip model creation.
    """
    trips = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            gross = _parse_decimal(row["AmountTotalPaid"])

            started_at = _parse_datetime(row["DateTripStart"])
            ended_at = _parse_datetime(row["DateTripEnd"])

            # Use "Time" column (HH:MM:SS) if available, else calculate from dates
            if row.get("Time", "").strip():
                duration = _parse_time_to_minutes(row["Time"])
            else:
                duration = round((ended_at - started_at).total_seconds() / 60, 2)

            trips.append({
                "source": "prima",
                "external_id": row["TripNumber"].strip(),
                "started_at": started_at,
                "ended_at": ended_at,
                "duration_minutes": duration,
                "gross_amount": gross,
                "commission": 0,
                "tips": _parse_decimal(row["AmountTips"]),
                "tolls": _parse_decimal(row["AmountTolls"]),
                "payout_amount": gross,
                "payment_method": row["PaymentMode"].strip().lower(),
                "distance_km": _parse_decimal(row["km"]),
                "km_free": _parse_decimal(row["kmFree"]) if row.get("kmFree", "").strip() else None,
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
                "_driver_code": row["DriverName"].strip(),
                "_driver_name": _CONDUCTOR_MAP.get(row.get("DriverNum", "").strip(), ""),
                "_license": row["License"].strip(),
            })
    return trips
