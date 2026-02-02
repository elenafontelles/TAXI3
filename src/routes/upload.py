# src/routes/upload.py
import os
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
from src.models.shift import Shift

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

PARSERS = {
    "uber": parse_uber_csv,
    "freenow": parse_freenow_csv,
    "prima": parse_prima_csv,
}

TRIP_FIELDS = {
    "source", "external_id", "started_at", "gross_amount", "commission",
    "tips", "tolls", "payout_amount", "payment_method", "distance_km",
    "duration_minutes", "origin_address", "dest_address",
}

SHIFT_FIELDS = {
    "source", "external_id", "started_at", "ended_at",
    "km_free", "km_occupied", "total_earnings",
}


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
    driver_id: str = Form(...),
    vehicle_id: str = Form(...),
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

    created = 0
    skipped = 0

    if platform == "prima":
        for s in records:
            existing = session.query(Shift).filter_by(external_id=s["external_id"]).first()
            if existing:
                skipped += 1
                continue
            model_data = {k: v for k, v in s.items() if k in SHIFT_FIELDS}
            shift = Shift(driver_id=driver_id, vehicle_id=vehicle_id, raw_data=s.get("raw_data"), **model_data)
            session.add(shift)
            created += 1
    else:
        for t in records:
            existing = session.query(Trip).filter_by(external_id=t["external_id"]).first()
            if existing:
                skipped += 1
                continue
            model_data = {k: v for k, v in t.items() if k in TRIP_FIELDS}
            trip = Trip(driver_id=driver_id, vehicle_id=vehicle_id, raw_data=t.get("raw_data"), **model_data)
            session.add(trip)
            created += 1

    session.commit()

    return await _render_result(
        request, session, user,
        success=f"Importados: {created} registros. Duplicados omitidos: {skipped}.",
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
