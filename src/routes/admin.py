# src/routes/admin.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.routes.auth import require_admin
from src.database import get_session
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.models.owner import Owner
from src.template_config import templates

router = APIRouter()


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: dict = Depends(require_admin), session: Session = Depends(get_session)):
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
async def edit_driver_page(driver_id: str, request: Request, user: dict = Depends(require_admin), session: Session = Depends(get_session)):
    driver = session.query(Driver).get(driver_id)
    if not driver:
        return RedirectResponse(url=request.scope.get("root_path", "") + "/admin", status_code=303)
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
    user: dict = Depends(require_admin),
    name: str = Form(...),
    email: str = Form(None),
    phone: str = Form(None),
    license_number: str = Form(...),
    commission_base_pct: float = Form(None),
    commission_bonus_pct: float = Form(None),
    commission_threshold: float = Form(None),
    freenow_commission_driver_pct: float = Form(None),
    uber_commission_driver_pct: float = Form(None),
    session: Session = Depends(get_session),
):
    driver = session.query(Driver).get(driver_id)
    if driver:
        driver.name = name
        driver.email = email or None
        driver.phone = phone or None
        driver.license_number = license_number
        driver.commission_base_pct = commission_base_pct if commission_base_pct is not None else 40
        driver.commission_bonus_pct = commission_bonus_pct if commission_bonus_pct is not None else 45
        driver.commission_threshold = commission_threshold if commission_threshold is not None else 300
        driver.freenow_commission_driver_pct = freenow_commission_driver_pct if freenow_commission_driver_pct is not None else 0
        driver.uber_commission_driver_pct = uber_commission_driver_pct if uber_commission_driver_pct is not None else 0
        session.commit()
    return RedirectResponse(url=request.scope.get("root_path", "") + "/admin", status_code=303)


# --- Vehicle endpoints ---

@router.get("/admin/vehicle/{vehicle_id}", response_class=HTMLResponse)
async def edit_vehicle_page(vehicle_id: str, request: Request, user: dict = Depends(require_admin), session: Session = Depends(get_session)):
    vehicle = session.query(Vehicle).get(vehicle_id)
    if not vehicle:
        return RedirectResponse(url=request.scope.get("root_path", "") + "/admin", status_code=303)
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
    user: dict = Depends(require_admin),
    plate: str = Form(...),
    license_number: str = Form(...),
    brand: str = Form(None),
    model: str = Form(None),
    year: int = Form(None),
    session: Session = Depends(get_session),
):
    vehicle = session.query(Vehicle).get(vehicle_id)
    if vehicle:
        vehicle.plate = plate
        vehicle.license_number = license_number
        vehicle.brand = brand or None
        vehicle.model = model or None
        vehicle.year = year
        session.commit()
    return RedirectResponse(url=request.scope.get("root_path", "") + "/admin", status_code=303)
