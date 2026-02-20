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
from src.models.other_expense import OtherExpense
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
    "distance_km", "km_free", "duration_minutes", "origin_address", "dest_address",
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
    # Mappings: 361-0397MSS, 092-8921LYW, 1061-2965MMM
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

    # Driver ID <-> Vehicle ID bidirectional mapping
    driver_id_to_vehicle = {}
    vehicle_id_to_driver = {}
    for d in drivers:
        lic = d.license_number.strip()
        if " - " in lic:
            lic_num = lic.split(" - ")[0].strip().lstrip("0")
            vid = license_to_vehicle.get(lic_num) or license_num_to_vehicle.get(lic_num)
            if vid:
                driver_id_to_vehicle[d.id] = vid
                vehicle_id_to_driver[vid] = d.id

    return {
        "driver_names": driver_names,
        "plate_to_vehicle": plate_to_vehicle,
        "license_to_driver": license_to_driver,
        "license_to_vehicle": license_to_vehicle,
        "license_num_to_vehicle": license_num_to_vehicle,
        "driver_id_to_vehicle": driver_id_to_vehicle,
        "vehicle_id_to_driver": vehicle_id_to_driver,
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

    # Fallback: if driver found but vehicle not, resolve via driver's license
    if not vehicle_id and driver_id:
        vehicle_id = lookups["driver_id_to_vehicle"].get(driver_id)

    # Fallback: if vehicle found but driver not, resolve via vehicle's driver
    if not driver_id and vehicle_id:
        driver_id = lookups["vehicle_id_to_driver"].get(vehicle_id)

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

    # Determine date range and source from parsed records
    source = records[0]["source"] if records else platform
    dates = [t["started_at"] for t in records if "started_at" in t]
    if dates:
        from datetime import date as date_type
        date_min = min(d.date() if hasattr(d, 'date') else d for d in dates)
        date_max = max(d.date() if hasattr(d, 'date') else d for d in dates)

        # Delete existing trips for this source in the date range
        from sqlalchemy import func
        deleted = session.query(Trip).filter(
            Trip.source == source,
            func.date(Trip.started_at) >= date_min,
            func.date(Trip.started_at) <= date_max,
        ).delete(synchronize_session=False)
    else:
        deleted = 0

    created = 0
    unmatched = 0
    new_trip_ids = []

    for t in records:
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

    msg = f"Importados: {created} nuevos."
    if deleted:
        msg += f" {deleted} registros anteriores reemplazados."
    if unmatched:
        msg += f" Sin asignar (conductor/vehiculo no encontrado): {unmatched}."
    if incidents:
        msg += f" Incidencias detectadas: {incidents}."
    return await _render_result(request, session, user, success=msg)


async def _process_fuel(request, user, platform, driver_id, vehicle_id, csv_file, session):
    """Handle Petroprix CSV or Repsol/Solred XLSX fuel upload with auto vehicle/driver matching."""
    if platform == "repsol":
        suffix = ".xlsx"
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
    provider = records[0]["provider"] if records else platform

    # Determine date range and plates from parsed records
    date_min = min(rec["date"] for rec in records)
    date_max = max(rec["date"] for rec in records)
    plates = {_normalize_plate(rec["_plate"]) for rec in records if "_plate" in rec}

    # Resolve vehicle IDs for the plates in the file
    vehicle_ids_to_delete = set()
    for plate in plates:
        vid = lookups["plate_to_vehicle"].get(plate)
        if vid:
            vehicle_ids_to_delete.add(vid)

    # Delete existing fuel records for these vehicles + provider in date range
    deleted = 0
    for vid in vehicle_ids_to_delete:
        deleted += session.query(FuelExpense).filter(
            FuelExpense.vehicle_id == vid,
            FuelExpense.provider == provider,
            FuelExpense.date >= date_min,
            FuelExpense.date <= date_max,
        ).delete()

    created = 0
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

    msg = f"Gastos combustible importados: {created} nuevos."
    if deleted:
        msg += f" {deleted} registros anteriores reemplazados."
    if unmatched:
        msg += f" Sin vehiculo asignado: {unmatched}."
    return await _render_result(request, session, user, success=msg)


async def _process_uber(request, user, csv_file, session):
    """Handle Uber payments CSV upload: import UberDailySummary records."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        content = await csv_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from scripts.parsers.uber_parser import parse_uber_csv
        records = parse_uber_csv(tmp_path)
    except Exception as e:
        os.unlink(tmp_path)
        return await _render_result(request, session, user, error=f"Error al parsear Uber CSV: {e}")

    os.unlink(tmp_path)

    if not records:
        return await _render_result(request, session, user, error="No se encontraron registros en el archivo")

    lookups = _build_lookups(session)
    source_file = csv_file.filename or "uber_upload"

    # Resolve driver names to license numbers
    resolved_records = []
    for rec in records:
        driver_name = rec.get("_driver_name", "").strip().lower()
        driver_id = None
        license_number = None

        # Match driver by name
        if driver_name:
            for db_name, db_id in lookups["driver_names"]:
                if driver_name == db_name or db_name.startswith(driver_name) or driver_name.startswith(db_name):
                    driver_id = db_id
                    break

        # Get license number from driver
        if driver_id:
            drivers = session.query(Driver).filter_by(id=driver_id).first()
            if drivers and drivers.license_number:
                lic = drivers.license_number.strip()
                if " - " in lic:
                    license_number = lic.split(" - ")[0].strip()
                else:
                    license_number = lic

        if license_number:
            rec["license_number"] = license_number
            rec["_driver_id"] = driver_id
            resolved_records.append(rec)

    if not resolved_records:
        return await _render_result(request, session, user, error="No se pudo resolver ningún conductor del archivo Uber")

    # Determine date range and license numbers
    license_numbers = {rec["license_number"] for rec in resolved_records}
    date_min = min(rec["date"] for rec in resolved_records)
    date_max = max(rec["date"] for rec in resolved_records)

    # Delete existing records in this range for these licenses
    deleted = 0
    for lic in license_numbers:
        deleted += session.query(UberDailySummary).filter(
            UberDailySummary.license_number == lic,
            UberDailySummary.date >= date_min,
            UberDailySummary.date <= date_max,
        ).delete()

    created = 0
    unmatched = 0

    for rec in resolved_records:
        lic_key = rec["license_number"].strip().lstrip("0")

        # Resolve vehicle by license number
        vehicle_id = lookups["license_num_to_vehicle"].get(lic_key)
        if not vehicle_id:
            vehicle_id = lookups["license_to_vehicle"].get(lic_key)

        summary = UberDailySummary(
            date=rec["date"],
            license_number=rec["license_number"],
            vehicle_id=vehicle_id,
            total_earnings=rec.get("total_earnings"),
            taximeter=rec.get("taximeter"),
            t3_fixed=rec["t3_fixed"],
            total_payment=rec["total_payment"],
            source_file=source_file,
        )
        session.add(summary)
        created += 1

        if not vehicle_id:
            unmatched += 1

    session.commit()

    msg = f"Resumen diario Uber importado: {created} nuevos."
    if deleted:
        msg += f" {deleted} registros anteriores reemplazados."
    if unmatched:
        msg += f" Sin vehiculo asignado: {unmatched}."
    return await _render_result(request, session, user, success=msg)


async def _process_lacaixa(request, user, vehicle_id, csv_file, session):
    """Handle La Caixa bank statement XLS/XLSX upload: import TpvDailyTotal records."""
    # Preserve original extension (.xls or .xlsx)
    orig_name = (csv_file.filename or "").lower()
    suffix = ".xls" if orig_name.endswith(".xls") and not orig_name.endswith(".xlsx") else ".xlsx"
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

    lookups = _build_lookups(session)
    source_file = csv_file.filename or "lacaixa_upload"

    # Determine date range and license numbers from parsed records
    license_numbers = {rec["license_number"] for rec in records}
    date_min = min(rec["date"] for rec in records)
    date_max = max(rec["date"] for rec in records)

    # Delete existing records in this range for these licenses
    # (ensures stale records from previous uploads are removed)
    deleted = 0
    for lic in license_numbers:
        deleted += session.query(TpvDailyTotal).filter(
            TpvDailyTotal.license_number == lic,
            TpvDailyTotal.date >= date_min,
            TpvDailyTotal.date <= date_max,
        ).delete()

    created = 0
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

    msg = f"Totales TPV importados: {created} nuevos."
    if deleted:
        msg += f" {deleted} registros anteriores reemplazados."
    if unmatched:
        msg += f" Sin vehiculo asignado: {unmatched}."
    return await _render_result(request, session, user, success=msg)


@router.post("/upload/otros-gastos", response_class=HTMLResponse)
async def add_other_expense(
    request: Request,
    user: dict = Depends(require_admin),
    driver_id: str = Form(...),
    fecha: str = Form(...),
    importe: float = Form(...),
    concepto: str = Form(...),
    session: Session = Depends(get_session),
):
    """Add a manual other expense entry."""
    from datetime import datetime
    try:
        expense_date = datetime.strptime(fecha.strip(), "%d/%m/%y").date()
    except ValueError:
        return await _render_result(request, session, user, error="Formato de fecha incorrecto. Usa DD/MM/YY")

    from decimal import Decimal
    expense = OtherExpense(
        date=expense_date,
        driver_id=driver_id,
        amount=Decimal(str(importe)),
        description=concepto.strip(),
        category="otro",
    )
    session.add(expense)
    session.commit()

    return await _render_result(
        request, session, user,
        success=f"Gasto registrado: {fecha} - {importe:.2f} EUR - {concepto}",
    )


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
