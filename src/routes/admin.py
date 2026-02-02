# src/routes/admin.py
import os
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.routes.auth import get_current_user
from src.database import get_session
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.models.owner import Owner

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


def _require_admin(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return None
    return user


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, session: Session = Depends(get_session)):
    user = _require_admin(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    drivers = session.query(Driver).filter_by(is_active=True).all()
    vehicles = session.query(Vehicle).filter_by(is_active=True).all()
    owners = session.query(Owner).filter_by(is_active=True).all()
    return templates.TemplateResponse(request, "admin.html", {
        "user": user,
        "drivers": drivers,
        "vehicles": vehicles,
        "owners": owners,
    })


# --- Driver endpoints ---

@router.get("/admin/driver/{driver_id}", response_class=HTMLResponse)
async def edit_driver_page(driver_id: str, request: Request, session: Session = Depends(get_session)):
    user = _require_admin(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    driver = session.query(Driver).get(driver_id)
    if not driver:
        return RedirectResponse(url="/admin", status_code=303)
    owners = session.query(Owner).filter_by(is_active=True).all()
    return templates.TemplateResponse(request, "admin_edit_driver.html", {
        "user": user,
        "driver": driver,
        "owners": owners,
    })


@router.post("/admin/driver/{driver_id}")
async def update_driver(
    driver_id: str,
    request: Request,
    name: str = Form(...),
    email: str = Form(None),
    phone: str = Form(None),
    license_number: str = Form(...),
    session: Session = Depends(get_session),
):
    user = _require_admin(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    driver = session.query(Driver).get(driver_id)
    if driver:
        driver.name = name
        driver.email = email or None
        driver.phone = phone or None
        driver.license_number = license_number
        session.commit()
    return RedirectResponse(url="/admin", status_code=303)


# --- Vehicle endpoints ---

@router.get("/admin/vehicle/{vehicle_id}", response_class=HTMLResponse)
async def edit_vehicle_page(vehicle_id: str, request: Request, session: Session = Depends(get_session)):
    user = _require_admin(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    vehicle = session.query(Vehicle).get(vehicle_id)
    if not vehicle:
        return RedirectResponse(url="/admin", status_code=303)
    owners = session.query(Owner).filter_by(is_active=True).all()
    return templates.TemplateResponse(request, "admin_edit_vehicle.html", {
        "user": user,
        "vehicle": vehicle,
        "owners": owners,
    })


@router.post("/admin/vehicle/{vehicle_id}")
async def update_vehicle(
    vehicle_id: str,
    request: Request,
    plate: str = Form(...),
    license_number: str = Form(...),
    brand: str = Form(None),
    model: str = Form(None),
    year: int = Form(None),
    session: Session = Depends(get_session),
):
    user = _require_admin(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    vehicle = session.query(Vehicle).get(vehicle_id)
    if vehicle:
        vehicle.plate = plate
        vehicle.license_number = license_number
        vehicle.brand = brand or None
        vehicle.model = model or None
        vehicle.year = year
        session.commit()
    return RedirectResponse(url="/admin", status_code=303)
