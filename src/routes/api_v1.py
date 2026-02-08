# src/routes/api_v1.py
"""REST API v1 — JSON endpoints for programmatic access."""
from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session
from src.database import get_session
from src.models.trip import Trip
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.models.sync_log import SyncLog
from src.models.pending_validation import PendingValidation
from src.models.visa_payment import VisaPayment
from src.models.fuel_expense import FuelExpense
from src.services.auth_service import decode_access_token

router = APIRouter(prefix="/api/v1", tags=["api"])


# ── Auth dependency (Bearer token) ────────────────────────────

def require_api_auth(authorization: str = Header(...)) -> dict:
    """Validate Bearer token and return user payload."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]
    user = decode_access_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def require_api_admin(user: dict = Depends(require_api_auth)) -> dict:
    if user.get("role") not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ── Auth ──────────────────────────────────────────────────────

@router.post("/auth/login")
async def api_login(
    email: str = Query(...),
    password: str = Query(...),
    session: Session = Depends(get_session),
):
    """Login and get a Bearer token."""
    from src.services.auth_service import verify_password, create_access_token
    driver = session.query(Driver).filter(Driver.email == email).first()
    if not driver or not verify_password(password, driver.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({
        "sub": driver.id,
        "role": "admin" if driver.is_owner else "driver",
        "name": driver.name,
    })
    return {"access_token": token, "token_type": "bearer"}


# ── Trips ─────────────────────────────────────────────────────

@router.get("/trips")
async def list_trips(
    user: dict = Depends(require_api_auth),
    session: Session = Depends(get_session),
    driver_id: str = Query(""),
    source: str = Query(""),
    date_from: str = Query(""),
    date_to: str = Query(""),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """List trips with optional filters and pagination."""
    q = session.query(Trip)

    # Drivers can only see their own trips
    if user.get("role") == "driver":
        q = q.filter(Trip.driver_id == user["sub"])
    elif driver_id:
        q = q.filter(Trip.driver_id == driver_id)

    if source:
        q = q.filter(Trip.source == source)
    if date_from:
        q = q.filter(cast(Trip.started_at, Date) >= date.fromisoformat(date_from))
    if date_to:
        q = q.filter(cast(Trip.started_at, Date) <= date.fromisoformat(date_to))

    total = q.count()
    trips = q.order_by(Trip.started_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [_trip_dict(t) for t in trips],
    }


@router.get("/trips/{trip_id}")
async def get_trip(
    trip_id: str,
    user: dict = Depends(require_api_auth),
    session: Session = Depends(get_session),
):
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if user.get("role") == "driver" and trip.driver_id != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return _trip_dict(trip)


# ── Drivers ───────────────────────────────────────────────────

@router.get("/drivers")
async def list_drivers(
    user: dict = Depends(require_api_admin),
    session: Session = Depends(get_session),
):
    drivers = session.query(Driver).filter_by(is_active=True).all()
    return [_driver_dict(d) for d in drivers]


@router.get("/drivers/{driver_id}")
async def get_driver(
    driver_id: str,
    user: dict = Depends(require_api_admin),
    session: Session = Depends(get_session),
):
    driver = session.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return _driver_dict(driver)


# ── Vehicles ──────────────────────────────────────────────────

@router.get("/vehicles")
async def list_vehicles(
    user: dict = Depends(require_api_admin),
    session: Session = Depends(get_session),
):
    vehicles = session.query(Vehicle).filter_by(is_active=True).all()
    return [_vehicle_dict(v) for v in vehicles]


# ── Summary / Aggregations ────────────────────────────────────

@router.get("/summary/daily")
async def daily_summary(
    user: dict = Depends(require_api_auth),
    session: Session = Depends(get_session),
    date_from: str = Query(""),
    date_to: str = Query(""),
    driver_id: str = Query(""),
):
    """Daily aggregated summary."""
    today = date.today()
    df = date.fromisoformat(date_from) if date_from else today.replace(day=1)
    dt = date.fromisoformat(date_to) if date_to else today

    q = (
        session.query(
            cast(Trip.started_at, Date).label("date"),
            Trip.driver_id,
            func.count(Trip.id).label("trip_count"),
            func.coalesce(func.sum(Trip.gross_amount), 0).label("gross"),
            func.coalesce(func.sum(Trip.commission), 0).label("commission"),
            func.coalesce(func.sum(Trip.payout_amount), 0).label("net"),
            func.coalesce(func.sum(Trip.distance_km), 0).label("km"),
        )
        .filter(cast(Trip.started_at, Date) >= df)
        .filter(cast(Trip.started_at, Date) <= dt)
        .group_by(cast(Trip.started_at, Date), Trip.driver_id)
        .order_by(cast(Trip.started_at, Date).desc())
    )

    if user.get("role") == "driver":
        q = q.filter(Trip.driver_id == user["sub"])
    elif driver_id:
        q = q.filter(Trip.driver_id == driver_id)

    drivers_map = {d.id: d.name for d in session.query(Driver).all()}

    return [
        {
            "date": str(r.date),
            "driver_id": r.driver_id,
            "driver_name": drivers_map.get(r.driver_id, "?"),
            "trip_count": r.trip_count,
            "gross": float(r.gross),
            "commission": float(r.commission),
            "net": float(r.net),
            "km": float(r.km),
        }
        for r in q.all()
    ]


@router.get("/summary/totals")
async def summary_totals(
    user: dict = Depends(require_api_auth),
    session: Session = Depends(get_session),
    date_from: str = Query(""),
    date_to: str = Query(""),
    driver_id: str = Query(""),
):
    """Period totals (today, this week, this month, custom range)."""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    df = date.fromisoformat(date_from) if date_from else start_of_month
    dt = date.fromisoformat(date_to) if date_to else today

    q = session.query(
        func.count(Trip.id).label("trips"),
        func.coalesce(func.sum(Trip.gross_amount), 0).label("gross"),
        func.coalesce(func.sum(Trip.commission), 0).label("commission"),
        func.coalesce(func.sum(Trip.payout_amount), 0).label("net"),
        func.coalesce(func.sum(Trip.distance_km), 0).label("km"),
        func.coalesce(func.sum(Trip.tips), 0).label("tips"),
    ).filter(
        cast(Trip.started_at, Date) >= df,
        cast(Trip.started_at, Date) <= dt,
    )

    if user.get("role") == "driver":
        q = q.filter(Trip.driver_id == user["sub"])
    elif driver_id:
        q = q.filter(Trip.driver_id == driver_id)

    row = q.one()
    return {
        "date_from": str(df),
        "date_to": str(dt),
        "trips": row.trips,
        "gross": float(row.gross),
        "commission": float(row.commission),
        "net": float(row.net),
        "km": float(row.km),
        "tips": float(row.tips),
    }


# ── Sync ──────────────────────────────────────────────────────

@router.get("/sync/logs")
async def sync_logs(
    user: dict = Depends(require_api_admin),
    session: Session = Depends(get_session),
    limit: int = Query(20, ge=1, le=100),
):
    logs = session.query(SyncLog).order_by(SyncLog.started_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "source": l.source,
            "sync_type": l.sync_type,
            "status": l.status,
            "records_found": l.records_found,
            "records_created": l.records_created,
            "records_skipped": l.records_skipped,
            "error_message": l.error_message,
            "started_at": l.started_at.isoformat() if l.started_at else None,
            "completed_at": l.completed_at.isoformat() if l.completed_at else None,
            "duration_seconds": float(l.duration_seconds) if l.duration_seconds else None,
        }
        for l in logs
    ]


@router.post("/sync/{source}")
async def trigger_sync(
    source: str,
    user: dict = Depends(require_api_admin),
    session: Session = Depends(get_session),
    start_date: str = Query(""),
    end_date: str = Query(""),
):
    """Trigger a sync job for FreeNow or Prima."""
    if source not in ("freenow", "prima"):
        raise HTTPException(status_code=400, detail="Source must be 'freenow' or 'prima'")

    from datetime import datetime, timezone
    from src.services.job_service import enqueue_sync

    yesterday = date.today() - timedelta(days=1)
    sd = date.fromisoformat(start_date) if start_date else yesterday
    ed = date.fromisoformat(end_date) if end_date else sd

    # Guard against double-runs
    already = session.query(SyncLog).filter_by(source=source, status="running").first()
    if already:
        raise HTTPException(status_code=409, detail=f"{source} sync already running")

    log = SyncLog(
        source=source,
        sync_type="api",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    session.add(log)
    session.commit()

    job_id = await enqueue_sync(source, log.id, sd, ed)
    return {"status": "queued", "log_id": log.id, "job_id": job_id}


# ── Validations ───────────────────────────────────────────────

@router.get("/validations")
async def list_validations(
    user: dict = Depends(require_api_admin),
    session: Session = Depends(get_session),
    status: str = Query("pending"),
    validation_type: str = Query(""),
):
    q = session.query(PendingValidation)
    if status:
        q = q.filter(PendingValidation.status == status)
    if validation_type:
        q = q.filter(PendingValidation.validation_type == validation_type)
    items = q.order_by(PendingValidation.created_at.desc()).all()
    return [
        {
            "id": pv.id,
            "trip_id": pv.trip_id,
            "validation_type": pv.validation_type,
            "status": pv.status,
            "details": pv.details,
            "created_at": pv.created_at.isoformat() if pv.created_at else None,
            "resolved_at": pv.resolved_at.isoformat() if pv.resolved_at else None,
            "resolved_by": pv.resolved_by,
        }
        for pv in items
    ]


@router.post("/validations/{validation_id}/resolve")
async def resolve_validation(
    validation_id: str,
    action: str = Query(...),
    user: dict = Depends(require_api_admin),
    session: Session = Depends(get_session),
):
    from datetime import datetime, timezone
    pv = session.get(PendingValidation, validation_id)
    if not pv:
        raise HTTPException(status_code=404, detail="Validation not found")
    if action not in ("valid", "invalid"):
        raise HTTPException(status_code=400, detail="Action must be 'valid' or 'invalid'")
    pv.status = action
    pv.resolved_at = datetime.now(timezone.utc)
    pv.resolved_by = user.get("name", "api")
    session.commit()
    return {"status": "ok", "validation_id": validation_id, "new_status": action}


# ── VISA Payments ─────────────────────────────────────────────

@router.get("/visa-payments")
async def list_visa_payments(
    user: dict = Depends(require_api_admin),
    session: Session = Depends(get_session),
    date_from: str = Query(""),
    date_to: str = Query(""),
    matched: str = Query(""),
):
    q = session.query(VisaPayment)
    if date_from:
        q = q.filter(VisaPayment.date >= date.fromisoformat(date_from))
    if date_to:
        q = q.filter(VisaPayment.date <= date.fromisoformat(date_to))
    if matched == "true":
        q = q.filter(VisaPayment.trip_id.isnot(None))
    elif matched == "false":
        q = q.filter(VisaPayment.trip_id.is_(None))

    payments = q.order_by(VisaPayment.date.desc(), VisaPayment.time.desc()).all()
    return [
        {
            "id": p.id,
            "date": p.date.isoformat(),
            "time": p.time.isoformat(),
            "amount": float(p.amount),
            "card_last4": p.card_last4,
            "brand": p.brand,
            "trip_id": p.trip_id,
            "tip_amount": float(p.tip_amount) if p.tip_amount else None,
            "vehicle_id": p.vehicle_id,
        }
        for p in payments
    ]


# ── Fuel Expenses ─────────────────────────────────────────────

@router.get("/fuel-expenses")
async def list_fuel_expenses(
    user: dict = Depends(require_api_admin),
    session: Session = Depends(get_session),
    date_from: str = Query(""),
    date_to: str = Query(""),
):
    q = session.query(FuelExpense)
    if date_from:
        q = q.filter(FuelExpense.date >= date.fromisoformat(date_from))
    if date_to:
        q = q.filter(FuelExpense.date <= date.fromisoformat(date_to))
    expenses = q.order_by(FuelExpense.date.desc()).all()
    return [
        {
            "id": e.id,
            "date": e.date.isoformat(),
            "vehicle_id": e.vehicle_id,
            "driver_id": e.driver_id,
            "liters": float(e.liters),
            "amount": float(e.amount),
            "provider": e.provider,
            "payment_method": e.payment_method,
        }
        for e in expenses
    ]


# ── Serializers ───────────────────────────────────────────────

def _trip_dict(t: Trip) -> dict:
    return {
        "id": t.id,
        "source": t.source,
        "external_id": t.external_id,
        "driver_id": t.driver_id,
        "vehicle_id": t.vehicle_id,
        "started_at": t.started_at.isoformat() if t.started_at else None,
        "ended_at": t.ended_at.isoformat() if t.ended_at else None,
        "duration_minutes": float(t.duration_minutes) if t.duration_minutes else None,
        "distance_km": float(t.distance_km) if t.distance_km else None,
        "gross_amount": float(t.gross_amount),
        "commission": float(t.commission),
        "taxes_vat": float(t.taxes_vat),
        "tips": float(t.tips),
        "tolls": float(t.tolls),
        "payout_amount": float(t.payout_amount) if t.payout_amount else None,
        "payment_method": t.payment_method,
        "tariff_code": t.tariff_code,
        "linked_trip_id": t.linked_trip_id,
        "origin_address": t.origin_address,
        "dest_address": t.dest_address,
    }


def _driver_dict(d: Driver) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "email": d.email,
        "phone": d.phone,
        "license_number": d.license_number,
        "is_owner": d.is_owner,
        "is_active": d.is_active,
        "commission_base_pct": float(d.commission_base_pct),
        "commission_bonus_pct": float(d.commission_bonus_pct),
        "commission_threshold": float(d.commission_threshold),
    }


def _vehicle_dict(v: Vehicle) -> dict:
    return {
        "id": v.id,
        "plate": v.plate,
        "license_number": v.license_number,
        "brand": v.brand,
        "model": v.model,
        "year": v.year,
        "is_active": v.is_active,
    }
