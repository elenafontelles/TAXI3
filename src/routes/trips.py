# src/routes/trips.py
import math
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from src.routes.auth import require_auth
from src.database import get_session
from src.services.trip_service import get_trips_list
from src.models.driver import Driver
from src.template_config import templates

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

    return templates.TemplateResponse(request, "trips.html", {
        "user": user,
        "trips": trips,
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "selected_source": source or "",
        "sort": sort,
        "order": order,
    })
