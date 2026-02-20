# src/routes/trips.py
import math
from datetime import date, datetime, time
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.routes.auth import require_auth
from src.database import get_session
from src.services.trip_service import get_trips_list
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.models.uber_daily_summary import UberDailySummary
from src.template_config import templates, root_path

router = APIRouter()


def _get_uber_summaries(session, sd, ed, driver_id, drivers_list):
    """Query UberDailySummary and format as trip-like dicts."""
    q = session.query(UberDailySummary)
    if sd:
        q = q.filter(UberDailySummary.date >= sd)
    if ed:
        q = q.filter(UberDailySummary.date <= ed)

    # If filtering by driver, resolve to license_number/vehicle_id
    if driver_id:
        driver = session.get(Driver, driver_id)
        if driver:
            lic = driver.license_number.strip()
            lic_num = lic.split(" - ")[0].strip() if " - " in lic else lic
            q = q.filter(UberDailySummary.license_number == lic_num)
        else:
            return []

    uber_rows = q.order_by(UberDailySummary.date.desc()).all()

    # Build license_number -> driver name map
    lic_to_driver = {}
    for d in drivers_list:
        lic = d.license_number.strip()
        lic_num = lic.split(" - ")[0].strip() if " - " in lic else lic
        lic_to_driver[lic_num] = d.name

    results = []
    for u in uber_rows:
        results.append({
            "started_at": u.date.strftime("%d/%m/%Y"),
            "sort_key": datetime.combine(u.date, time.min),
            "source": "uber",
            "driver_name": lic_to_driver.get(u.license_number, u.license_number),
            "gross_amount": f"{float(u.total_earnings or 0):.2f}",
            "payout_amount": f"{float(u.total_payment or 0):.2f}",
        })
    return results


@router.get("/trips", response_class=HTMLResponse)
async def trips_page(
    request: Request,
    user: dict = Depends(require_auth),
    source: str = Query(""),
    driver_id: str = Query(""),
    start_date: str = Query(""),
    end_date: str = Query(""),
    page: int = Query(1, ge=1),
    sort: str = Query("started_at"),
    order: str = Query("desc"),
    session: Session = Depends(get_session),
):
    if order not in ("asc", "desc"):
        order = "desc"

    # Role-based driver filter
    filter_driver_id = user["sub"] if user.get("role") == "driver" else (driver_id or None)

    # Parse dates
    sd = date.fromisoformat(start_date) if start_date else None
    ed = date.fromisoformat(end_date) if end_date else None

    # Driver list for filter dropdown
    drivers_list = session.query(Driver).filter(Driver.is_active == True).order_by(Driver.name).all()

    # Get Trip records (prima, freenow) — exclude uber from Trip table
    include_trips = source != "uber"
    include_uber = source in ("", "uber")

    trips = []

    if include_trips:
        trip_source = source if source else None
        # If showing all, exclude uber from Trip query (uber comes from UberDailySummary)
        if not trip_source:
            trip_source = None  # get_trips_list will return all sources
        per_page_trips = 500  # get all for merging, paginate after
        trips_raw, _ = get_trips_list(
            session,
            driver_id=filter_driver_id,
            source=trip_source,
            start_date=sd,
            end_date=ed,
            page=1, per_page=per_page_trips, sort="started_at", order="desc",
        )

        # Driver name cache
        all_driver_ids = {t.driver_id for t in trips_raw}
        if all_driver_ids:
            rows = session.query(Driver.id, Driver.name).filter(Driver.id.in_(all_driver_ids)).all()
            driver_cache = {r.id: r.name for r in rows}
        else:
            driver_cache = {}

        for t in trips_raw:
            # Skip uber Trip records (stale data from before parser rewrite)
            if t.source == "uber":
                continue
            trips.append({
                "started_at": t.started_at.strftime("%d/%m/%Y %H:%M"),
                "sort_key": t.started_at,
                "source": t.source,
                "driver_name": driver_cache.get(t.driver_id, "Desconocido"),
                "gross_amount": f"{t.gross_amount:.2f}",
                "payout_amount": f"{t.payout_amount:.2f}" if t.payout_amount else "—",
            })

    # Get Uber daily summaries
    if include_uber:
        uber_trips = _get_uber_summaries(session, sd, ed, filter_driver_id, drivers_list)
        trips.extend(uber_trips)

    # Sort combined results
    reverse = order == "desc"
    if sort == "started_at":
        trips.sort(key=lambda x: x.get("sort_key", datetime.min), reverse=reverse)
    elif sort == "gross_amount":
        trips.sort(key=lambda x: float(x.get("gross_amount", 0)), reverse=reverse)
    elif sort == "source":
        trips.sort(key=lambda x: x.get("source", ""), reverse=reverse)
    elif sort == "driver_id":
        trips.sort(key=lambda x: x.get("driver_name", ""), reverse=reverse)

    # Paginate
    total = len(trips)
    per_page = 50
    total_pages = math.ceil(total / per_page) if total else 1
    start_idx = (page - 1) * per_page
    trips_page = trips[start_idx:start_idx + per_page]

    return templates.TemplateResponse(request, "trips.html", {
        "user": user,
        "trips": trips_page,
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "selected_source": source or "",
        "selected_driver_id": driver_id or "",
        "start_date": start_date,
        "end_date": end_date,
        "sort": sort,
        "order": order,
        "drivers": drivers_list,
    })
