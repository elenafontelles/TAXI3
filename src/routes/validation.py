# src/routes/validation.py
from datetime import date, datetime
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.routes.auth import require_admin
from src.database import get_session
from src.models.pending_validation import PendingValidation
from src.models.trip import Trip
from src.models.vehicle import Vehicle
from src.template_config import templates, root_path

router = APIRouter()


@router.get("/validacion", response_class=HTMLResponse)
async def validation_page(
    request: Request,
    start_date: str = "",
    end_date: str = "",
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    incidents = session.query(PendingValidation).filter_by(
        validation_type="incident", status="pending"
    ).all()

    # Parse date filters
    sd = date.fromisoformat(start_date) if start_date else None
    ed = date.fromisoformat(end_date) if end_date else None

    incident_trips = {}
    incident_vehicles = {}
    filtered_incidents = []
    for pv in incidents:
        if pv.trip_id:
            trip = session.get(Trip, pv.trip_id)
            if trip and float(trip.gross_amount or 0) != 0:
                # Filter by date range using trip started_at
                trip_date = trip.started_at.date() if trip.started_at else None
                if sd and trip_date and trip_date < sd:
                    continue
                if ed and trip_date and trip_date > ed:
                    continue
                incident_trips[pv.id] = trip
                if trip.vehicle_id:
                    vehicle = session.get(Vehicle, trip.vehicle_id)
                    if vehicle:
                        incident_vehicles[pv.id] = vehicle.plate
                filtered_incidents.append(pv)

    return templates.TemplateResponse(request, "validation.html", {
        "user": user,
        "start_date": start_date,
        "end_date": end_date,
        "incidents": filtered_incidents,
        "incident_trips": incident_trips,
        "incident_vehicles": incident_vehicles,
        "total_pending": len(filtered_incidents),
    })


@router.post("/validacion/{validation_id}/resolve", response_class=HTMLResponse)
async def resolve_validation(
    request: Request,
    validation_id: str,
    action: str = Form(...),
    start_date: str = Form(""),
    end_date: str = Form(""),
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    from datetime import timezone
    pv = session.get(PendingValidation, validation_id)
    if not pv:
        return RedirectResponse(url=f"{root_path}/validacion", status_code=303)
    if action == "valid":
        pv.status = "valid"
    elif action == "invalid":
        pv.status = "invalid"
    pv.resolved_at = datetime.now(timezone.utc)
    pv.resolved_by = user.get("name", "admin")
    session.commit()
    params = ""
    if start_date or end_date:
        params = f"?start_date={start_date}&end_date={end_date}"
    return RedirectResponse(url=f"{root_path}/validacion{params}", status_code=303)
