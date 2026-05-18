# src/services/import_service.py
"""Shared CSV import logic used by /upload and /descargar-csvs."""
import logging
import os
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.models.trip import Trip
from src.models.pending_validation import PendingValidation
from src.models.visa_payment import VisaPayment
from src.models.uber_daily_summary import UberDailySummary
from src.routes.upload import _build_lookups, _resolve_driver_vehicle, TRIP_FIELDS

logger = logging.getLogger(__name__)


def import_csv_file(filepath: str, platform: str, session: Session) -> str:
    """Import a CSV using the replace strategy (delete range + reimport).

    Returns a human-readable result message.
    """
    if platform == "uber":
        return _import_uber(filepath, session)
    elif platform in ("freenow", "prima"):
        return _import_trips(filepath, platform, session)
    else:
        raise ValueError(f"Plataforma no soportada: {platform}")


def _import_trips(filepath: str, platform: str, session: Session) -> str:
    """Import FreeNow or Prima CSV with replace strategy."""
    from scripts.parsers.freenow_parser import parse_freenow_csv
    from scripts.parsers.prima_parser import parse_prima_csv

    parser = parse_freenow_csv if platform == "freenow" else parse_prima_csv
    records = parser(filepath)

    if not records:
        return "No se encontraron registros en el archivo"

    lookups = _build_lookups(session)
    source = records[0].get("source", platform)

    # Determine date range
    dates = [t["started_at"] for t in records if "started_at" in t]
    if dates:
        date_min = min(d.date() if hasattr(d, "date") else d for d in dates)
        date_max = max(d.date() if hasattr(d, "date") else d for d in dates)

        # Delete existing trips in range (replace strategy)
        trip_ids = [
            t.id for t in session.query(Trip.id).filter(
                Trip.source == source,
                func.date(Trip.started_at) >= date_min,
                func.date(Trip.started_at) <= date_max,
            ).all()
        ]
        if trip_ids:
            session.query(PendingValidation).filter(
                PendingValidation.trip_id.in_(trip_ids)
            ).delete(synchronize_session=False)
            session.query(VisaPayment).filter(
                VisaPayment.trip_id.in_(trip_ids)
            ).delete(synchronize_session=False)
            session.query(Trip).filter(
                Trip.linked_trip_id.in_(trip_ids)
            ).update({Trip.linked_trip_id: None}, synchronize_session=False)

        deleted = session.query(Trip).filter(
            Trip.source == source,
            func.date(Trip.started_at) >= date_min,
            func.date(Trip.started_at) <= date_max,
        ).delete(synchronize_session=False)
    else:
        deleted = 0

    created = unmatched = 0
    new_trip_ids = []

    for t in records:
        row_driver, row_vehicle = _resolve_driver_vehicle(t, lookups, "", "")
        if not row_driver or not row_vehicle:
            unmatched += 1
            continue

        model_data = {k: v for k, v in t.items() if k in TRIP_FIELDS}
        trip = Trip(
            driver_id=row_driver, vehicle_id=row_vehicle,
            raw_data=t.get("raw_data"), **model_data,
        )
        session.add(trip)
        session.flush()
        new_trip_ids.append(trip.id)
        created += 1

    session.commit()

    from src.services.incident_detector import create_incident_validations
    incidents = create_incident_validations(session, new_trip_ids)

    msg = f"Importados: {created} viajes."
    if deleted:
        msg += f" {deleted} anteriores reemplazados."
    if unmatched:
        msg += f" Sin asignar: {unmatched}."
    if incidents:
        msg += f" Incidencias: {incidents}."
    return msg


def _import_uber(filepath: str, session: Session) -> str:
    """Import Uber CSV with replace strategy."""
    from scripts.parsers.uber_parser import parse_uber_csv
    from src.models.driver import Driver

    records = parse_uber_csv(filepath)
    if not records:
        return "No se encontraron registros en el archivo Uber"

    lookups = _build_lookups(session)

    # Resolve driver names to license numbers
    resolved = []
    for rec in records:
        driver_name = rec.get("_driver_name", "").strip().lower()
        driver_id = None
        license_number = None

        if driver_name:
            for db_name, db_id in lookups["driver_names"]:
                if (driver_name == db_name
                        or db_name.startswith(driver_name)
                        or driver_name.startswith(db_name)):
                    driver_id = db_id
                    break

        if driver_id:
            driver = session.query(Driver).filter_by(id=driver_id).first()
            if driver and driver.license_number:
                lic = driver.license_number.strip()
                license_number = lic.split(" - ")[0].strip() if " - " in lic else lic

        if license_number:
            rec["license_number"] = license_number
            rec["_driver_id"] = driver_id
            resolved.append(rec)

    if not resolved:
        return "No se pudo resolver ningun conductor del archivo Uber"

    # Delete existing records in range (replace strategy)
    license_numbers = {r["license_number"] for r in resolved}
    date_min = min(r["date"] for r in resolved)
    date_max = max(r["date"] for r in resolved)

    deleted = 0
    for lic in license_numbers:
        deleted += session.query(UberDailySummary).filter(
            UberDailySummary.license_number == lic,
            UberDailySummary.date >= date_min,
            UberDailySummary.date <= date_max,
        ).delete()

    created = 0
    for rec in resolved:
        lic_key = rec["license_number"].strip().lstrip("0")
        vehicle_id = (lookups["license_num_to_vehicle"].get(lic_key)
                      or lookups["license_to_vehicle"].get(lic_key))

        summary = UberDailySummary(
            date=rec["date"],
            license_number=rec["license_number"],
            vehicle_id=vehicle_id,
            total_earnings=rec.get("total_earnings"),
            taximeter=rec.get("taximeter"),
            t3_fixed=rec["t3_fixed"],
            total_payment=rec["total_payment"],
            source_file=os.path.basename(filepath),
        )
        session.add(summary)
        created += 1

    session.commit()

    msg = f"Uber importado: {created} resumenes diarios."
    if deleted:
        msg += f" {deleted} anteriores reemplazados."
    return msg
