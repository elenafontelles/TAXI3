"""Import CSV files from a directory into the database.

Detects the platform source from the filename prefix (uber_, freenow_, prima_)
and routes to the appropriate parser. Supports duplicate detection via
external_id to prevent re-importing the same records.

Usage:
    from scripts.import_csvs import import_csv_files
    result = import_csv_files("/path/to/imports", db_session,
                              default_driver_id="...", default_vehicle_id="...")
"""
import os
import glob
from sqlalchemy.orm import Session
from scripts.parsers.uber_parser import parse_uber_csv
from scripts.parsers.freenow_parser import parse_freenow_csv
from scripts.parsers.prima_parser import parse_prima_csv
from src.models.trip import Trip
from src.models.shift import Shift


# Fields from parsed dicts that map directly to Trip model columns
TRIP_FIELDS = {
    "source", "external_id", "started_at", "gross_amount", "commission",
    "tips", "tolls", "payout_amount", "payment_method", "distance_km",
    "duration_minutes", "origin_address", "dest_address",
}

# Fields from parsed dicts that map directly to Shift model columns
SHIFT_FIELDS = {
    "source", "external_id", "started_at", "ended_at",
    "km_free", "km_occupied", "total_earnings",
}


def detect_source(filename: str) -> str | None:
    """Detect the platform source from a CSV filename.

    Returns 'uber', 'freenow', 'prima', or None if unrecognized.
    """
    name = os.path.basename(filename).lower()
    if name.startswith("uber"):
        return "uber"
    elif name.startswith("freenow"):
        return "freenow"
    elif name.startswith("prima"):
        return "prima"
    return None


def import_csv_files(
    import_dir: str,
    session: Session,
    default_driver_id: str = None,
    default_vehicle_id: str = None,
) -> dict:
    """Import all CSV files from import_dir into the database.

    Args:
        import_dir: Directory containing CSV files to import.
        session: SQLAlchemy database session.
        default_driver_id: Driver ID to assign to imported records.
        default_vehicle_id: Vehicle ID to assign to imported records.

    Returns:
        Dict with keys: files_processed, records_created, records_skipped, errors.
    """
    result = {
        "files_processed": 0,
        "records_created": 0,
        "records_skipped": 0,
        "errors": [],
    }

    csv_files = glob.glob(os.path.join(import_dir, "*.csv"))

    for filepath in csv_files:
        source = detect_source(filepath)
        if not source:
            result["errors"].append(f"Unknown source: {filepath}")
            continue

        try:
            if source == "prima":
                shifts = parse_prima_csv(filepath)
                for s in shifts:
                    existing = (
                        session.query(Shift)
                        .filter_by(external_id=s["external_id"])
                        .first()
                    )
                    if existing:
                        result["records_skipped"] += 1
                        continue
                    model_data = {k: v for k, v in s.items() if k in SHIFT_FIELDS}
                    shift = Shift(
                        driver_id=default_driver_id,
                        vehicle_id=default_vehicle_id,
                        raw_data=s.get("raw_data"),
                        **model_data,
                    )
                    session.add(shift)
                    result["records_created"] += 1
            else:
                if source == "uber":
                    trips = parse_uber_csv(filepath)
                else:
                    trips = parse_freenow_csv(filepath)

                for t in trips:
                    existing = (
                        session.query(Trip)
                        .filter_by(external_id=t["external_id"])
                        .first()
                    )
                    if existing:
                        result["records_skipped"] += 1
                        continue
                    model_data = {k: v for k, v in t.items() if k in TRIP_FIELDS}
                    trip = Trip(
                        driver_id=default_driver_id,
                        vehicle_id=default_vehicle_id,
                        raw_data=t.get("raw_data"),
                        **model_data,
                    )
                    session.add(trip)
                    result["records_created"] += 1

            session.commit()
            result["files_processed"] += 1
        except Exception as e:
            session.rollback()
            result["errors"].append(f"Error processing {filepath}: {str(e)}")

    return result
