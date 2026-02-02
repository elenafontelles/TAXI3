# src/routes/trips.py
import os
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.routes.auth import get_current_user
from src.database import get_session
from src.services.trip_service import get_trips_list
from src.models.driver import Driver

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/trips", response_class=HTMLResponse)
async def trips_page(request: Request, source: str = Query(None), session: Session = Depends(get_session)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    driver_id = user["sub"] if user.get("role") == "driver" else None
    trips_raw = get_trips_list(session, driver_id=driver_id, source=source if source else None)

    # Build display data with driver names
    driver_cache = {}
    trips = []
    for t in trips_raw:
        if t.driver_id not in driver_cache:
            d = session.query(Driver).filter_by(id=t.driver_id).first()
            driver_cache[t.driver_id] = d.name if d else "Desconocido"
        trips.append({
            "started_at": t.started_at.strftime("%d/%m/%Y %H:%M"),
            "source": t.source,
            "driver_name": driver_cache[t.driver_id],
            "gross_amount": f"{t.gross_amount:.2f}",
            "payout_amount": f"{t.payout_amount:.2f}" if t.payout_amount else "—",
        })

    return templates.TemplateResponse(request, "trips.html", {
        "user": user,
        "trips": trips,
        "selected_source": source or "",
    })
