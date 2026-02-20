# src/routes/validation.py
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
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    incidents = session.query(PendingValidation).filter_by(
        validation_type="incident", status="pending"
    ).all()

    incident_trips = {}
    incident_vehicles = {}
    filtered_incidents = []
    for pv in incidents:
        if pv.trip_id:
            trip = session.get(Trip, pv.trip_id)
            if trip and float(trip.gross_amount or 0) != 0:
                incident_trips[pv.id] = trip
                if trip.vehicle_id:
                    vehicle = session.get(Vehicle, trip.vehicle_id)
                    if vehicle:
                        incident_vehicles[pv.id] = vehicle.plate
                filtered_incidents.append(pv)

    return templates.TemplateResponse(request, "validation.html", {
        "user": user,
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
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    from datetime import datetime, timezone
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
    return RedirectResponse(url=f"{root_path}/validacion", status_code=303)
