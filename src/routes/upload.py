# src/routes/upload.py
import os
import re
import tempfile
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.routes.auth import get_current_user
from src.database import get_session
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from scripts.parsers.uber_parser import parse_uber_csv
from scripts.parsers.freenow_parser import parse_freenow_csv
from scripts.parsers.prima_parser import parse_prima_csv
from src.models.trip import Trip

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

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
async def upload_page(request: Request, session: Session = Depends(get_session)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=303)
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
    platform: str = Form(...),
    driver_id: str = Form(""),
    vehicle_id: str = Form(""),
    csv_file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=303)

    parser = PARSERS.get(platform)
    if not parser:
        return await _render_result(request, session, user, error="Plataforma no reconocida")

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        content = await csv_file.read()
        tmp.write(content)
        tmp_path = tmp.name

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
        created += 1

    session.commit()

    msg = f"Importados: {created} registros. Duplicados omitidos: {skipped}."
    if unmatched:
        msg += f" Sin asignar (conductor/vehiculo no encontrado): {unmatched}."
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
