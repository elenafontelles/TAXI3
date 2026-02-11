# src/routes/upload.py
import logging
import os
import re
import tempfile
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.routes.auth import require_admin
from src.database import get_session
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from scripts.parsers.freenow_parser import parse_freenow_csv
from scripts.parsers.prima_parser import parse_prima_csv
from src.models.trip import Trip
from src.models.fuel_expense import FuelExpense
from src.models.tpv_daily_total import TpvDailyTotal
from src.models.uber_daily_summary import UberDailySummary
from src.template_config import templates

logger = logging.getLogger(__name__)

router = APIRouter()

PARSERS = {
    "freenow": parse_freenow_csv,
    "prima": parse_prima_csv,
}

TRIP_FIELDS = {
    "source", "external_id", "started_at", "ended_at", "gross_amount",
    "commission", "taxes_vat", "tips", "tolls", "payout_amount", "payment_method",
    "distance_km", "duration_minutes", "origin_address", "dest_address",
    "origin_lat", "origin_lng", "dest_lat", "dest_lng", "tariff_code",
    "fare_type",
}


def _normalize_plate(plate: str) -> str:
    """Strip spaces, dashes, dots for plate comparison."""
    return re.sub(r"[\s\-\.]", "", plate).upper()


def _build_lookups(session: Session) -> dict:
    """Build lookup dicts for auto-matching drivers and vehicles."""
    drivers = session.query(Driver).filter_by(is_active=True).all()
    vehicles = session.query(Vehicle).filter_by(is_active=True).all()

    # FreeNow: match by driver name (case-insensitive, supports partial match)
    driver_names = []
    for d in drivers:
        driver_names.append((d.name.strip().lower(), d.id))

    # FreeNow: match vehicle by normalized plate
    plate_to_vehicle = {}
    for v in vehicles:
        plate_to_vehicle[_normalize_plate(v.plate)] = v.id

    # Prima: match driver by license number prefix
    # Driver license_number format: "092 - 8921LYW" -> extract "092"
    license_to_driver = {}
    license_to_vehicle = {}
    for d in drivers:
        lic = d.license_number.strip()
        # Extract the numeric license part before " - "
        if " - " in lic:
            lic_num = lic.split(" - ")[0].strip().lstrip("0")
            plate_part = lic.split(" - ")[1].strip()
            license_to_driver[lic_num] = d.id
            # Find the vehicle by plate embedded in the license
            norm = _normalize_plate(plate_part)
            if norm in plate_to_vehicle:
                license_to_vehicle[lic_num] = plate_to_vehicle[norm]

    # License number to vehicle (from vehicles table)
    license_num_to_vehicle = {}
    for v in vehicles:
        lic = v.license_number.strip().lstrip("0")
        license_num_to_vehicle[lic] = v.id

    return {
        "driver_names": driver_names,
        "plate_to_vehicle": plate_to_vehicle,
        "license_to_driver": license_to_driver,
        "license_to_vehicle": license_to_vehicle,
        "license_num_to_vehicle": license_num_to_vehicle,
    }


def _resolve_driver_vehicle(record: dict, lookups: dict, fallback_driver: str, fallback_vehicle: str) -> tuple[str | None, str | None]:
    """Resolve driver_id and vehicle_id from CSV record metadata."""
    driver_id = None
    vehicle_id = None

    # FreeNow: match by name + plate (supports partial: "Ivan Alsina" matches "Ivan Alsina Burgos")
    if "_driver_name" in record:
        name_key = record["_driver_name"].strip().lower()
        if name_key:
            for db_name, db_id in lookups["driver_names"]:
                if name_key == db_name or db_name.startswith(name_key) or name_key.startswith(db_name):
                    driver_id = db_id
                    break
    if "_plate" in record:
        plate_key = _normalize_plate(record["_plate"])
        vehicle_id = lookups["plate_to_vehicle"].get(plate_key)

    # Prima: match by license number
    if "_license" in record:
        lic_key = record["_license"].strip().lstrip("0")
        if not driver_id:
            driver_id = lookups["license_to_driver"].get(lic_key)
        if not vehicle_id:
            vehicle_id = lookups["license_to_vehicle"].get(lic_key)

    # Fallback to form selection
    return driver_id or fallback_driver, vehicle_id or fallback_vehicle


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request, user: dict = Depends(require_admin), session: Session = Depends(get_session)):
    drivers = session.query(Driver).filter_by(is_active=True).all()
    vehicles = session.query(Vehicle).filter_by(is_active=True).all()
    return templates.TemplateResponse(request, "upload.html", {
        "user": user,
        "drivers": drivers,
        "vehicles": vehicles,
    })


@router.post("/upload/process", response_class=HTMLResponse)
async def process_upload(
    request: Request,
    user: dict = Depends(require_admin),
    platform: str = Form(...),
    driver_id: str = Form(""),
    vehicle_id: str = Form(""),
    csv_file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    # La Caixa bank statement upload (XLSX, different flow)
    if platform == "lacaixa":
        return await _process_lacaixa(request, user, vehicle_id, csv_file, session)

    # Uber daily summary upload (XLSX, different flow)
    if platform == "uber":
        return await _process_uber(request, user, csv_file, session)

    # Fuel upload (Petroprix CSV / Repsol PDF)
    if platform in ("petroprix", "repsol"):
        return await _process_fuel(request, user, platform, driver_id, vehicle_id, csv_file, session)

    parser = PARSERS.get(platform)
    if not parser:
        return await _render_result(request, session, user, error="Plataforma no reconocida")

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        content = await csv_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Validate CSV schema before parsing
    from src.services.csv_validator import validate_csv_schema
    is_valid, validation_error = validate_csv_schema(tmp_path, platform)
    if not is_valid:
        os.unlink(tmp_path)
        return await _render_result(request, session, user, error=validation_error)

    try:
        records = parser(tmp_path)
    except Exception as e:
        os.unlink(tmp_path)
        return await _render_result(request, session, user, error=f"Error al parsear CSV: {e}")

    os.unlink(tmp_path)

    lookups = _build_lookups(session)
    created = 0
    updated = 0
    unmatched = 0
    new_trip_ids = []

    for t in records:
        row_driver, row_vehicle = _resolve_driver_vehicle(t, lookups, driver_id, vehicle_id)
        if not row_driver or not row_vehicle:
            unmatched += 1
            continue

        model_data = {k: v for k, v in t.items() if k in TRIP_FIELDS}
        existing = session.query(Trip).filter_by(external_id=t["external_id"], source=t["source"]).first()
        if existing:
            for key, val in model_data.items():
                setattr(existing, key, val)
            existing.driver_id = row_driver
            existing.vehicle_id = row_vehicle
            existing.raw_data = t.get("raw_data")
            updated += 1
        else:
            trip = Trip(driver_id=row_driver, vehicle_id=row_vehicle, raw_data=t.get("raw_data"), **model_data)
            session.add(trip)
            session.flush()
            new_trip_ids.append(trip.id)
            created += 1

    session.commit()

    # Auto-detect incidents in newly imported trips
    from src.services.incident_detector import create_incident_validations
    incidents = create_incident_validations(session, new_trip_ids)

    msg = f"Importados: {created} nuevos, {updated} actualizados."
    if unmatched:
        msg += f" Sin asignar (conductor/vehiculo no encontrado): {unmatched}."
    if incidents:
        msg += f" Incidencias detectadas: {incidents}."
    return await _render_result(request, session, user, success=msg)


async def _process_fuel(request, user, platform, driver_id, vehicle_id, csv_file, session):
    """Handle Petroprix CSV or Repsol PDF fuel upload with auto vehicle/driver matching."""
    if platform == "repsol":
        suffix = ".pdf"
    else:
        suffix = ".csv"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await csv_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Validate CSV schema for Petroprix
    if platform == "petroprix":
        from src.services.csv_validator import validate_csv_schema
        is_valid, validation_error = validate_csv_schema(tmp_path, platform)
        if not is_valid:
            os.unlink(tmp_path)
            return await _render_result(request, session, user, error=validation_error)

    try:
        if platform == "petroprix":
            from scripts.parsers.petroprix_parser import parse_petroprix_csv
            records = parse_petroprix_csv(tmp_path)
        else:
            from scripts.parsers.repsol_parser import parse_repsol_pdf
            records = parse_repsol_pdf(tmp_path)
    except Exception as e:
        os.unlink(tmp_path)
        return await _render_result(request, session, user, error=f"Error al parsear {platform}: {e}")

    os.unlink(tmp_path)

    if not records:
        return await _render_result(request, session, user, error="No se encontraron registros en el archivo")

    lookups = _build_lookups(session)
    source_file = csv_file.filename or f"{platform}_upload"
    created = 0
    updated = 0
    unmatched = 0

    for rec in records:
        # Resolve vehicle from _plate
        rec_vehicle = vehicle_id
        if "_plate" in rec:
            plate_key = _normalize_plate(rec["_plate"])
            matched_vehicle = lookups["plate_to_vehicle"].get(plate_key)
            if matched_vehicle:
                rec_vehicle = matched_vehicle

        # Resolve driver from _driver name or fallback
        rec_driver = driver_id or None
        if "_driver" in rec and rec["_driver"]:
            name_key = rec["_driver"].strip().lower()
            if name_key:
                for db_name, db_id in lookups["driver_names"]:
                    if name_key == db_name or db_name.startswith(name_key) or name_key.startswith(db_name):
                        rec_driver = db_id
                        break

        if not rec_vehicle:
            unmatched += 1
            continue

        # Upsert by date + vehicle + amount + provider
        existing = session.query(FuelExpense).filter_by(
            date=rec["date"],
            vehicle_id=rec_vehicle,
            amount=rec["amount"],
            provider=rec["provider"],
        ).first()
        if existing:
            existing.driver_id = rec_driver
            existing.liters = rec["liters"]
            existing.source_file = source_file
            existing.payment_method = rec.get("payment_method", "tarjeta")
            updated += 1
        else:
            expense = FuelExpense(
                date=rec["date"],
                vehicle_id=rec_vehicle,
                driver_id=rec_driver,
                liters=rec["liters"],
                amount=rec["amount"],
                provider=rec["provider"],
                source_file=source_file,
                payment_method=rec.get("payment_method", "tarjeta"),
            )
            session.add(expense)
            created += 1

    session.commit()

    msg = f"Gastos combustible importados: {created} nuevos, {updated} actualizados."
    if unmatched:
        msg += f" Sin vehiculo asignado: {unmatched}."
    return await _render_result(request, session, user, success=msg)


async def _process_uber(request, user, csv_file, session):
    """Handle Uber daily summary XLSX upload: import UberDailySummary records."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        content = await csv_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from scripts.parsers.uber_parser import parse_uber_xlsx
        records = parse_uber_xlsx(tmp_path)
    except Exception as e:
        os.unlink(tmp_path)
        return await _render_result(request, session, user, error=f"Error al parsear Uber XLSX: {e}")

    os.unlink(tmp_path)

    if not records:
        return await _render_result(request, session, user, error="No se encontraron registros en el archivo")

    lookups = _build_lookups(session)
    source_file = csv_file.filename or "uber_upload"
    created = 0
    updated = 0
    unmatched = 0

    for rec in records:
        lic_key = rec["license_number"].strip().lstrip("0")

        # Resolve vehicle by license number
        vehicle_id = lookups["license_num_to_vehicle"].get(lic_key)
        if not vehicle_id:
            vehicle_id = lookups["license_to_vehicle"].get(lic_key)

        # Upsert by date + license_number
        existing = session.query(UberDailySummary).filter_by(
            date=rec["date"],
            license_number=rec["license_number"],
        ).first()
        if existing:
            existing.vehicle_id = vehicle_id
            existing.total_earnings = rec["total_earnings"]
            existing.taximeter = rec["taximeter"]
            existing.refund = rec["refund"]
            existing.adjustments = rec["adjustments"]
            existing.t3_fixed = rec["t3_fixed"]
            existing.total_payment = rec["total_payment"]
            existing.source_file = source_file
            updated += 1
        else:
            summary = UberDailySummary(
                date=rec["date"],
                license_number=rec["license_number"],
                vehicle_id=vehicle_id,
                total_earnings=rec["total_earnings"],
                taximeter=rec["taximeter"],
                refund=rec["refund"],
                adjustments=rec["adjustments"],
                t3_fixed=rec["t3_fixed"],
                total_payment=rec["total_payment"],
                source_file=source_file,
            )
            session.add(summary)
            created += 1

        if not vehicle_id:
            unmatched += 1

    session.commit()

    msg = f"Resumen diario Uber importado: {created} nuevos, {updated} actualizados."
    if unmatched:
        msg += f" Sin vehiculo asignado: {unmatched}."
    return await _render_result(request, session, user, success=msg)


async def _process_lacaixa(request, user, vehicle_id, csv_file, session):
    """Handle La Caixa bank statement XLSX upload: import TpvDailyTotal records."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        content = await csv_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from scripts.parsers.lacaixa_parser import parse_lacaixa_xlsx
        records = parse_lacaixa_xlsx(tmp_path)
    except Exception as e:
        os.unlink(tmp_path)
        return await _render_result(request, session, user, error=f"Error al parsear La Caixa XLSX: {e}")

    os.unlink(tmp_path)

    if not records:
        return await _render_result(request, session, user, error="No se encontraron registros en el archivo")

    lookups = _build_lookups(session)
    source_file = csv_file.filename or "lacaixa_upload"
    created = 0
    updated = 0
    unmatched = 0

    for rec in records:
        lic_key = rec["license_number"].strip().lstrip("0")

        # Resolve vehicle by license number
        rec_vehicle = lookups["license_num_to_vehicle"].get(lic_key)
        if not rec_vehicle:
            rec_vehicle = lookups["license_to_vehicle"].get(lic_key)
        if not rec_vehicle:
            rec_vehicle = vehicle_id

        if not rec_vehicle:
            unmatched += 1
            continue

        # Upsert by date + license_number
        existing = session.query(TpvDailyTotal).filter_by(
            date=rec["date"],
            license_number=rec["license_number"],
        ).first()
        if existing:
            existing.vehicle_id = rec_vehicle
            existing.amount = rec["amount"]
            existing.source_file = source_file
            updated += 1
        else:
            total = TpvDailyTotal(
                date=rec["date"],
                vehicle_id=rec_vehicle,
                license_number=rec["license_number"],
                amount=rec["amount"],
                source_file=source_file,
            )
            session.add(total)
            created += 1

    session.commit()

    msg = f"Totales TPV importados: {created} nuevos, {updated} actualizados."
    if unmatched:
        msg += f" Sin vehiculo asignado: {unmatched}."
    return await _render_result(request, session, user, success=msg)


async def _render_result(request, session, user, success=None, error=None):
    drivers = session.query(Driver).filter_by(is_active=True).all()
    vehicles = session.query(Vehicle).filter_by(is_active=True).all()
    return templates.TemplateResponse(request, "upload.html", {
        "user": user,
        "drivers": drivers,
        "vehicles": vehicles,
        "success": success,
        "error": error,
    })
