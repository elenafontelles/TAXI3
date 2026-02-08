# src/routes/sync.py
import csv
import logging
import os
from datetime import datetime, date, timedelta, timezone
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.routes.auth import require_admin
from src.database import get_session
from src.models.sync_log import SyncLog
from src.models.trip import Trip
from scripts.parsers.freenow_parser import parse_freenow_csv
from scripts.parsers.prima_parser import parse_prima_csv
from src.routes.upload import _build_lookups, _resolve_driver_vehicle, TRIP_FIELDS
from src.template_config import templates, root_path
from src.services.job_service import enqueue_sync

logger = logging.getLogger(__name__)

router = APIRouter()

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
    new_trip_ids = []

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
        session.flush()
        new_trip_ids.append(trip.id)
        created += 1

    session.commit()

    # Auto-detect incidents
    from src.services.incident_detector import create_incident_validations
    create_incident_validations(session, new_trip_ids)

    return created, skipped, unmatched


@router.get("/sync", response_class=HTMLResponse)
async def sync_page(request: Request, user: dict = Depends(require_admin), session: Session = Depends(get_session)):
    platform_status = _get_platform_status(session)
    import_files = _list_import_files()
    sync_logs = (session.query(SyncLog)
                 .order_by(SyncLog.started_at.desc())
                 .limit(50).all())
    has_running_sync = any(l.status == "running" for l in sync_logs)

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    return templates.TemplateResponse(request, "sync.html", {
        "user": user,
        "platform_status": platform_status,
        "import_files": import_files,
        "sync_logs": sync_logs,
        "has_running_sync": has_running_sync,
        "default_start": week_ago,
        "default_end": yesterday,
    })


@router.post("/sync/freenow", response_class=HTMLResponse)
async def sync_freenow(
    request: Request,
    user: dict = Depends(require_admin),
    start_date: str = Form(""),
    end_date: str = Form(""),
    session: Session = Depends(get_session),
):
    # Guard against double-runs
    already_running = (session.query(SyncLog)
                       .filter_by(source="freenow", status="running")
                       .first())
    if already_running:
        return RedirectResponse(url=f"{root_path}/sync", status_code=303)

    # Parse dates (default: yesterday)
    yesterday = date.today() - timedelta(days=1)
    sd = date.fromisoformat(start_date) if start_date else yesterday
    ed = date.fromisoformat(end_date) if end_date else sd

    log = SyncLog(
        source="freenow",
        sync_type="scraper",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    session.add(log)
    session.commit()
    log_id = log.id

    # Enqueue job to Redis (processed by Arq worker)
    await enqueue_sync("freenow", log_id, sd, ed)

    return RedirectResponse(url=f"{root_path}/sync", status_code=303)


def _import_prima_csv(csv_path: str, session: Session) -> tuple[int, int, int]:
    """Import a Prima CSV file. Returns (created, skipped, unmatched)."""
    records = parse_prima_csv(csv_path)
    lookups = _build_lookups(session)
    created = skipped = unmatched = 0
    new_trip_ids = []

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
        session.flush()
        new_trip_ids.append(trip.id)
        created += 1

    session.commit()

    # Auto-detect incidents
    from src.services.incident_detector import create_incident_validations
    create_incident_validations(session, new_trip_ids)

    return created, skipped, unmatched


@router.post("/sync/prima", response_class=HTMLResponse)
async def sync_prima(
    request: Request,
    user: dict = Depends(require_admin),
    start_date: str = Form(""),
    end_date: str = Form(""),
    session: Session = Depends(get_session),
):
    # Guard against double-runs
    already_running = (session.query(SyncLog)
                       .filter_by(source="prima", status="running")
                       .first())
    if already_running:
        return RedirectResponse(url=f"{root_path}/sync", status_code=303)

    # Parse dates (default: yesterday)
    yesterday = date.today() - timedelta(days=1)
    sd = date.fromisoformat(start_date) if start_date else yesterday
    ed = date.fromisoformat(end_date) if end_date else sd

    log = SyncLog(
        source="prima",
        sync_type="scraper",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    session.add(log)
    session.commit()
    log_id = log.id

    # Enqueue job to Redis (processed by Arq worker)
    await enqueue_sync("prima", log_id, sd, ed)

    return RedirectResponse(url=f"{root_path}/sync", status_code=303)


@router.post("/sync/cross-match", response_class=HTMLResponse)
async def cross_match(
    request: Request,
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Manually run cross-matching of Prima trips with FreeNow/Uber."""
    from src.services.trip_matcher import cross_match_trips
    stats = cross_match_trips(session)

    # Redirect back with result in query params
    msg = f"Enlazados: {stats['matched']}, Sin enlace: {stats['no_match']}"
    return RedirectResponse(
        url=f"{root_path}/sync?cross_match_result={msg}",
        status_code=303,
    )


@router.get("/sync/files/{filename}", response_class=HTMLResponse)
async def view_import_file(
    request: Request,
    filename: str,
    user: dict = Depends(require_admin),
):
    # Security: only allow simple filenames (no path traversal)
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files supported")

    filepath = os.path.join(IMPORTS_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    headers = []
    rows = []
    with open(filepath, newline="", encoding="utf-8") as f:
        # Detect delimiter
        sample = f.read(4096)
        f.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.reader(f, delimiter=delimiter)
        headers = next(reader, [])
        for row in reader:
            rows.append(row)

    return templates.TemplateResponse(request, "sync_file_view.html", {
        "user": user,
        "filename": filename,
        "headers": headers,
        "rows": rows,
        "total_rows": len(rows),
    })
