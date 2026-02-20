# src/routes/validation.py
from datetime import date, datetime, time, timedelta, timezone
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
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
    sd = date.fromisoformat(start_date) if start_date else None
    ed = date.fromisoformat(end_date) if end_date else None

    incidents = []
    incident_vehicles = {}

    if sd and ed:
        # Query trips directly: incident criteria + date range + non-zero amount
        trips = session.query(Trip).filter(
            Trip.source == "prima",
            Trip.distance_km == 0,
            Trip.duration_minutes < 0.5,
            Trip.gross_amount != 0,
            Trip.started_at >= datetime.combine(sd, time.min),
            Trip.started_at < datetime.combine(ed + timedelta(days=1), time.min),
        ).order_by(Trip.started_at).all()

        # Get existing PendingValidation status for each trip
        for trip in trips:
            pv = session.query(PendingValidation).filter_by(
                trip_id=trip.id, validation_type="incident"
            ).first()

            # Skip already resolved (valid or invalid)
            if pv and pv.status in ("valid", "invalid"):
                continue

            # Create PendingValidation if it doesn't exist yet
            if not pv:
                pv = PendingValidation(
                    trip_id=trip.id,
                    validation_type="incident",
                    status="pending",
                    details={
                        "distance_km": float(trip.distance_km or 0),
                        "duration_minutes": float(trip.duration_minutes or 0),
                    },
                )
                session.add(pv)
                session.flush()

            incidents.append({"pv": pv, "trip": trip})

            if trip.vehicle_id:
                vehicle = session.get(Vehicle, trip.vehicle_id)
                if vehicle:
                    incident_vehicles[pv.id] = vehicle.plate

        session.commit()

    return templates.TemplateResponse(request, "validation.html", {
        "user": user,
        "start_date": start_date,
        "end_date": end_date,
        "incidents": incidents,
        "incident_vehicles": incident_vehicles,
        "total_pending": len(incidents),
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
