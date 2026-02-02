# src/routes/sync.py
import os
import re
from datetime import datetime, date, timedelta, timezone
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.routes.auth import get_current_user
from src.database import get_session
from src.models.sync_log import SyncLog
from src.models.trip import Trip
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from scripts.parsers.freenow_parser import parse_freenow_csv
from src.routes.upload import _build_lookups, _resolve_driver_vehicle, TRIP_FIELDS

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

IMPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "imports")


def _get_platform_status(session: Session) -> dict:
    """Get last successful sync per platform."""
    result = {}
    for source in ("uber", "freenow", "prima"):
        last = (session.query(SyncLog)
                .filter_by(source=source, status="success")
                .order_by(SyncLog.completed_at.desc())
                .first())
        result[source] = last
    return result


def _list_import_files() -> list[dict]:
    """List CSV files in the imports directory."""
    files = []
    if not os.path.isdir(IMPORTS_DIR):
        return files
    for name in sorted(os.listdir(IMPORTS_DIR), reverse=True):
        if not name.endswith(".csv"):
            continue
        path = os.path.join(IMPORTS_DIR, name)
        stat = os.stat(path)
        # Parse source from filename (e.g. "freenow_2026-01-01_to_2026-02-02.csv")
        source = name.split("_")[0] if "_" in name else "unknown"
        files.append({
            "name": name,
            "source": source,
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
        })
    return files


def _import_freenow_csv(csv_path: str, session: Session) -> tuple[int, int, int]:
    """Import a FreeNow CSV file. Returns (created, skipped, unmatched)."""
    records = parse_freenow_csv(csv_path)
    lookups = _build_lookups(session)
    created = skipped = unmatched = 0

    for t in records:
        existing = session.query(Trip).filter_by(
            external_id=t["external_id"], source=t["source"]).first()
        if existing:
            skipped += 1
            continue

        row_driver, row_vehicle = _resolve_driver_vehicle(t, lookups, "", "")
        if not row_driver or not row_vehicle:
            unmatched += 1
            continue

        model_data = {k: v for k, v in t.items() if k in TRIP_FIELDS}
        trip = Trip(driver_id=row_driver, vehicle_id=row_vehicle,
                    raw_data=t.get("raw_data"), **model_data)
        session.add(trip)
        created += 1

    session.commit()
    return created, skipped, unmatched


@router.get("/sync", response_class=HTMLResponse)
async def sync_page(request: Request, session: Session = Depends(get_session)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=303)

    platform_status = _get_platform_status(session)
    import_files = _list_import_files()
    sync_logs = (session.query(SyncLog)
                 .order_by(SyncLog.started_at.desc())
                 .limit(50).all())

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    return templates.TemplateResponse(request, "sync.html", {
        "user": user,
        "platform_status": platform_status,
        "import_files": import_files,
        "sync_logs": sync_logs,
        "default_date": yesterday,
    })


@router.post("/sync/freenow", response_class=HTMLResponse)
async def sync_freenow(
    request: Request,
    start_date: str = Form(""),
    end_date: str = Form(""),
    session: Session = Depends(get_session),
):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=303)

    started_at = datetime.now(timezone.utc)
    log = SyncLog(
        source="freenow",
        sync_type="scraper",
        status="running",
        started_at=started_at,
    )
    session.add(log)
    session.commit()

    try:
        # Parse dates (default: yesterday)
        yesterday = date.today() - timedelta(days=1)
        sd = date.fromisoformat(start_date) if start_date else yesterday
        ed = date.fromisoformat(end_date) if end_date else sd

        # Run scraper
        from scrapers.freenow_scraper import FreeNowScraper
        scraper = FreeNowScraper(start_date=sd, end_date=ed)
        csv_path = scraper.run()

        if not csv_path:
            log.status = "error"
            log.error_message = "No se pudo descargar el CSV (sin datos o credenciales incorrectas)"
            log.completed_at = datetime.now(timezone.utc)
            log.duration_seconds = (log.completed_at - started_at).total_seconds()
            session.commit()
            return RedirectResponse(url="/sync?error=download_failed", status_code=303)

        # Import CSV
        created, skipped, unmatched = _import_freenow_csv(csv_path, session)

        log.status = "success"
        log.records_found = created + skipped + unmatched
        log.records_created = created
        log.records_skipped = skipped
        log.completed_at = datetime.now(timezone.utc)
        log.duration_seconds = (log.completed_at - started_at).total_seconds()
        if unmatched:
            log.error_message = f"{unmatched} viajes sin conductor/vehiculo asignado"
        session.commit()

        return RedirectResponse(url="/sync?success=freenow", status_code=303)

    except Exception as e:
        log.status = "error"
        log.error_message = str(e)[:500]
        log.completed_at = datetime.now(timezone.utc)
        log.duration_seconds = (log.completed_at - started_at).total_seconds()
        session.commit()
        return RedirectResponse(url="/sync?error=freenow_exception", status_code=303)
