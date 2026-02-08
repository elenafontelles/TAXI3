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
from scripts.parsers.uber_parser import parse_uber_csv
from scripts.parsers.freenow_parser import parse_freenow_csv
from scripts.parsers.prima_parser import parse_prima_csv
from src.models.trip import Trip
from src.models.visa_payment import VisaPayment
from src.models.fuel_expense import FuelExpense
from src.models.pending_validation import PendingValidation
from src.template_config import templates

logger = logging.getLogger(__name__)

router = APIRouter()

PARSERS = {
    "uber": parse_uber_csv,
    "freenow": parse_freenow_csv,
    "prima": parse_prima_csv,
}

TRIP_FIELDS = {
    "source", "external_id", "started_at", "ended_at", "gross_amount",
    "commission", "taxes_vat", "tips", "tolls", "payout_amount", "payment_method",
    "distance_km", "duration_minutes", "origin_address", "dest_address",
    "origin_lat", "origin_lng", "dest_lat", "dest_lng", "tariff_code",
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

    return {
        "driver_names": driver_names,
        "plate_to_vehicle": plate_to_vehicle,
        "license_to_driver": license_to_driver,
        "license_to_vehicle": license_to_vehicle,
    }


def _resolve_driver_vehicle(record: dict, lookups: dict, fallback_driver: str, fallback_vehicle: str) -> tuple[str | None, str | None]:
    """Resolve driver_id and vehicle_id from CSV record metadata."""
    driver_id = None
    vehicle_id = None

    # FreeNow: match by name + plate (supports partial: "Ivan Alsina" matches "Ivan Alsina Burgos")
    if "_driver_name" in record:
        name_key = record["_driver_name"].strip().lower()
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
    # La Caixa VISA upload (XLSX, different flow)
    if platform == "lacaixa":
        return await _process_lacaixa(request, user, vehicle_id, csv_file, session)

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
    skipped = 0
    unmatched = 0
    new_trip_ids = []

    for t in records:
        existing = session.query(Trip).filter_by(external_id=t["external_id"], source=t["source"]).first()
        if existing:
            skipped += 1
            continue

        row_driver, row_vehicle = _resolve_driver_vehicle(t, lookups, driver_id, vehicle_id)
        if not row_driver or not row_vehicle:
            unmatched += 1
            continue

        model_data = {k: v for k, v in t.items() if k in TRIP_FIELDS}
        trip = Trip(driver_id=row_driver, vehicle_id=row_vehicle, raw_data=t.get("raw_data"), **model_data)
        session.add(trip)
        session.flush()
        new_trip_ids.append(trip.id)
        created += 1

    session.commit()

    # Auto-detect incidents in newly imported trips
    from src.services.incident_detector import create_incident_validations
    incidents = create_incident_validations(session, new_trip_ids)

    msg = f"Importados: {created} registros. Duplicados omitidos: {skipped}."
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
    skipped = 0
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
            for db_name, db_id in lookups["driver_names"]:
                if name_key == db_name or db_name.startswith(name_key) or name_key.startswith(db_name):
                    rec_driver = db_id
                    break

        if not rec_vehicle:
            unmatched += 1
            continue

        # Deduplicate by date + vehicle + amount + provider
        existing = session.query(FuelExpense).filter_by(
            date=rec["date"],
            vehicle_id=rec_vehicle,
            amount=rec["amount"],
            provider=rec["provider"],
        ).first()
        if existing:
            skipped += 1
            continue

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

    msg = f"Gastos combustible importados: {created}. Duplicados: {skipped}."
    if unmatched:
        msg += f" Sin vehiculo asignado: {unmatched}."
    return await _render_result(request, session, user, success=msg)


async def _process_lacaixa(request, user, vehicle_id, csv_file, session):
    """Handle La Caixa VISA XLSX upload: import payments and auto-match to trips."""
    suffix = ".xlsx" if csv_file.filename and csv_file.filename.endswith(".xlsx") else ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
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

    # Resolve vehicle from license in file or form selection
    license_num = records[0].get("_license")
    if not vehicle_id and license_num:
        lookups = _build_lookups(session)
        vehicle_id = lookups["license_to_vehicle"].get(license_num.lstrip("0"), "")

    if not vehicle_id:
        return await _render_result(request, session, user, error="No se pudo determinar el vehiculo. Selecciona uno manualmente.")

    source_file = csv_file.filename or "lacaixa_upload"
    created = 0
    skipped = 0
    new_payment_ids = []

    for rec in records:
        # Deduplicate by date+time+amount+card
        existing = session.query(VisaPayment).filter_by(
            date=rec["date"], time=rec["time"],
            amount=rec["amount"], card_last4=rec["card_last4"],
            vehicle_id=vehicle_id,
        ).first()
        if existing:
            skipped += 1
            continue

        payment = VisaPayment(
            date=rec["date"],
            time=rec["time"],
            terminal_id=rec["terminal_id"],
            card_last4=rec["card_last4"],
            brand=rec["brand"],
            amount=rec["amount"],
            vehicle_id=vehicle_id,
            source_file=source_file,
        )
        session.add(payment)
        session.flush()
        new_payment_ids.append(payment.id)
        created += 1

    session.commit()

    # Auto-match VISA payments to trips
    from src.services.visa_matcher import match_visa_to_trip
    matched = 0
    unmatched_ids = []

    from datetime import datetime, timedelta

    for pid in new_payment_ids:
        payment = session.get(VisaPayment, pid)
        if not payment:
            continue

        # Find trips on the same day for the same vehicle
        day_start = datetime.combine(payment.date, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        trips = session.query(Trip).filter(
            Trip.vehicle_id == vehicle_id,
            Trip.started_at >= day_start,
            Trip.started_at < day_end,
        ).all()

        trip_dicts = [
            {"id": t.id, "ended_at": t.ended_at, "gross_amount": float(t.gross_amount)}
            for t in trips if t.ended_at
        ]

        result = match_visa_to_trip(
            {"date": payment.date, "time": payment.time, "amount": payment.amount},
            trip_dicts,
        )

        if result:
            payment.trip_id = result["trip_id"]
            payment.tip_amount = result["tip_amount"]
            matched += 1
        else:
            unmatched_ids.append(pid)

    # Create PendingValidation for unmatched payments
    for pid in unmatched_ids:
        payment = session.get(VisaPayment, pid)
        if not payment:
            continue
        pv = PendingValidation(
            validation_type="visa_no_match",
            status="pending",
            details={
                "visa_payment_id": pid,
                "date": payment.date.isoformat(),
                "time": payment.time.isoformat(),
                "amount": float(payment.amount),
                "card_last4": payment.card_last4,
                "brand": payment.brand,
            },
        )
        session.add(pv)

    session.commit()

    # Notify about unmatched VISA payments
    if unmatched_ids:
        from src.services.email_service import notify_pending_validations
        await notify_pending_validations(len(unmatched_ids))

    msg = f"Pagos VISA importados: {created}. Duplicados: {skipped}. Enlazados con viaje: {matched}."
    if unmatched_ids:
        msg += f" Sin enlace (pendientes de validacion): {len(unmatched_ids)}."
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
