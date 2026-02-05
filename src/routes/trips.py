# src/routes/trips.py
import math
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.routes.auth import require_auth, require_admin
from src.database import get_session
from src.services.trip_service import get_trips_list
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.models.trip import Trip
from src.template_config import templates, root_path

router = APIRouter()


@router.get("/trips", response_class=HTMLResponse)
async def trips_page(
    request: Request,
    user: dict = Depends(require_auth),
    source: str = Query(None),
    page: int = Query(1, ge=1),
    sort: str = Query("started_at"),
    order: str = Query("desc"),
    session: Session = Depends(get_session),
):
    if order not in ("asc", "desc"):
        order = "desc"

    driver_id = user["sub"] if user.get("role") == "driver" else None
    per_page = 50
    trips_raw, total = get_trips_list(
        session, driver_id=driver_id, source=source if source else None,
        page=page, per_page=per_page, sort=sort, order=order,
    )
    total_pages = math.ceil(total / per_page) if total else 1

    driver_ids = {t.driver_id for t in trips_raw}
    if driver_ids:
        rows = session.query(Driver.id, Driver.name).filter(Driver.id.in_(driver_ids)).all()
        driver_cache = {r.id: r.name for r in rows}
    else:
        driver_cache = {}

    trips = []
    for t in trips_raw:
        trips.append({
            "started_at": t.started_at.strftime("%d/%m/%Y %H:%M"),
            "source": t.source,
            "driver_name": driver_cache.get(t.driver_id, "Desconocido"),
            "gross_amount": f"{t.gross_amount:.2f}",
            "payout_amount": f"{t.payout_amount:.2f}" if t.payout_amount else "—",
        })

    # Get drivers and vehicles for the manual entry form (admin only)
    drivers_list = []
    vehicles_list = []
    if user.get("role") == "admin":
        drivers_list = session.query(Driver).filter(Driver.is_active == True).order_by(Driver.name).all()
        vehicles_list = session.query(Vehicle).filter(Vehicle.is_active == True).order_by(Vehicle.plate).all()

    return templates.TemplateResponse(request, "trips.html", {
        "user": user,
        "trips": trips,
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "selected_source": source or "",
        "sort": sort,
        "order": order,
        "drivers": drivers_list,
        "vehicles": vehicles_list,
    })


@router.post("/trips/uber", response_class=HTMLResponse)
async def create_uber_trip(
    request: Request,
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
    trip_date: str = Form(...),
    trip_time: str = Form(...),
    driver_id: str = Form(...),
    vehicle_id: str = Form(...),
    gross_amount: str = Form(...),
    tips: str = Form("0"),
    payment_method: str = Form(""),
):
    """Create a manual Uber trip entry."""
    # Parse datetime
    dt_str = f"{trip_date} {trip_time}"
    started_at = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    started_at = started_at.replace(tzinfo=timezone.utc)

    # Parse amounts
    gross = float(gross_amount.replace(",", "."))
    tips_amount = float(tips.replace(",", ".")) if tips else 0.0

    # Generate external_id for manual entries
    external_id = f"manual-{uuid.uuid4().hex[:8]}"

    trip = Trip(
        source="uber",
        external_id=external_id,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        started_at=started_at,
        gross_amount=gross,
        tips=tips_amount,
        payment_method=payment_method if payment_method else None,
        payout_amount=gross + tips_amount,  # Simplified: gross + tips
        raw_data={"manual_entry": True, "created_by": user.get("sub")},
    )
    session.add(trip)
    session.commit()

    return RedirectResponse(url=f"{root_path}/trips?source=uber", status_code=303)
