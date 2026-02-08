# src/routes/summary.py
from datetime import date, timedelta
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from src.routes.auth import require_admin
from src.database import get_session
from src.models.trip import Trip
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.template_config import templates

router = APIRouter()


def _get_daily_summaries(session: Session, date_from: date, date_to: date, driver_id: str | None = None) -> list[dict]:
    """Aggregate trips by date and driver."""
    q = (
        session.query(
            cast(Trip.started_at, Date).label("date"),
            Trip.driver_id,
            Trip.vehicle_id,
            func.count(Trip.id).label("trip_count"),
            func.coalesce(func.sum(Trip.gross_amount), 0).label("gross_amount"),
            func.coalesce(func.sum(Trip.commission), 0).label("commission"),
            func.coalesce(func.sum(Trip.payout_amount), 0).label("net_amount"),
            func.coalesce(func.sum(Trip.distance_km), 0).label("total_km"),
        )
        .filter(cast(Trip.started_at, Date) >= date_from)
        .filter(cast(Trip.started_at, Date) <= date_to)
        .group_by(cast(Trip.started_at, Date), Trip.driver_id, Trip.vehicle_id)
        .order_by(cast(Trip.started_at, Date).desc())
    )
    if driver_id:
        q = q.filter(Trip.driver_id == driver_id)

    # Build lookup dicts
    drivers = {d.id: d.name for d in session.query(Driver).all()}
    vehicles = {v.id: v.plate for v in session.query(Vehicle).all()}

    results = []
    for row in q.all():
        results.append({
            "date": row.date,
            "driver_name": drivers.get(row.driver_id, "?"),
            "vehicle": vehicles.get(row.vehicle_id, "?"),
            "trip_count": row.trip_count,
            "gross_amount": f"{float(row.gross_amount):.2f}",
            "commission": f"{float(row.commission):.2f}",
            "net_amount": f"{float(row.net_amount):.2f}",
            "total_km": f"{float(row.total_km):.1f}",
        })
    return results


def _get_monthly_totals(session: Session, date_from: date, date_to: date, driver_id: str | None = None) -> dict:
    """Get totals for the period."""
    q = (
        session.query(
            func.count(Trip.id).label("trips"),
            func.coalesce(func.sum(Trip.gross_amount), 0).label("gross"),
            func.coalesce(func.sum(Trip.commission), 0).label("commission"),
            func.coalesce(func.sum(Trip.payout_amount), 0).label("net"),
            func.coalesce(func.sum(Trip.distance_km), 0).label("km"),
        )
        .filter(cast(Trip.started_at, Date) >= date_from)
        .filter(cast(Trip.started_at, Date) <= date_to)
    )
    if driver_id:
        q = q.filter(Trip.driver_id == driver_id)
    row = q.one()
    return {
        "trips": row.trips,
        "gross": f"{float(row.gross):.2f}",
        "commission": f"{float(row.commission):.2f}",
        "net": f"{float(row.net):.2f}",
        "km": f"{float(row.km):.1f}",
    }


@router.get("/summary", response_class=HTMLResponse)
async def summary_page(
    request: Request,
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
    date_from: str = Query(""),
    date_to: str = Query(""),
    driver_id: str = Query(""),
):
    today = date.today()
    df = date.fromisoformat(date_from) if date_from else today.replace(day=1)
    dt = date.fromisoformat(date_to) if date_to else today

    did = driver_id if driver_id else None
    summaries = _get_daily_summaries(session, df, dt, did)
    totals = _get_monthly_totals(session, df, dt, did)

    drivers = session.query(Driver).filter_by(is_active=True).all()

    return templates.TemplateResponse(request, "summary.html", {
        "user": user,
        "summaries": summaries,
        "totals": totals,
        "drivers": drivers,
        "date_from": df.isoformat(),
        "date_to": dt.isoformat(),
        "selected_driver": driver_id,
    })
