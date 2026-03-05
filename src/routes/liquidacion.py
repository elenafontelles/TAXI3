# src/routes/liquidacion.py
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

LOCAL_TZ = ZoneInfo("Europe/Madrid")
from src.routes.auth import require_admin
from src.database import get_session
from src.models.driver import Driver
from src.models.trip import Trip
from src.models.tpv_daily_total import TpvDailyTotal
from src.models.uber_daily_summary import UberDailySummary
from src.models.fuel_expense import FuelExpense
from src.models.other_expense import OtherExpense
from src.models.freenow_adjustment import FreenowAdjustment
from src.models.vehicle import Vehicle
from src.models.pending_validation import PendingValidation
from src.services.settlement_calculator import calculate_daily_settlement
from src.services.excel_exporter import export_settlement_to_excel
from src.services.pdf_exporter import export_settlement_to_pdf
from src.template_config import templates, root_path

router = APIRouter()


def _extract_license_number(driver: Driver) -> str | None:
    """Extract numeric license from driver's license_number field.

    Driver license_number format: "361 - 0397MSS" or "092 - 8921LYW"
    Returns: "361", "092", etc.
    """
    lic = driver.license_number.strip()
    if " - " in lic:
        return lic.split(" - ")[0].strip()
    return lic


def _normalize_plate(plate: str) -> str:
    """Strip spaces, dashes, dots for plate comparison."""
    import re
    return re.sub(r"[\s\-\.]", "", plate).upper()


def _resolve_vehicle(session: Session, driver: Driver) -> Vehicle | None:
    """Resolve vehicle from driver's license_number.

    Tries multiple strategies:
    1. Match Vehicle.license_number by taxi license (e.g. "361")
    2. Match Vehicle.plate by plate embedded in driver.license_number (e.g. "0397MSS")
    """
    lic = driver.license_number.strip()
    lic_num = _extract_license_number(driver)

    # Strategy 1: match by license number
    if lic_num:
        vehicle = session.query(Vehicle).filter(
            Vehicle.license_number == lic_num,
            Vehicle.is_active == True,
        ).first()
        if vehicle:
            return vehicle

        # Try with leading zeros stripped
        vehicles = session.query(Vehicle).filter_by(is_active=True).all()
        for v in vehicles:
            if v.license_number.strip().lstrip("0") == lic_num.lstrip("0"):
                return v

    # Strategy 2: match by plate from "361 - 0397MSS" format
    if " - " in lic:
        plate_part = lic.split(" - ")[1].strip()
        if plate_part:
            norm_plate = _normalize_plate(plate_part)
            vehicles = session.query(Vehicle).filter_by(is_active=True).all()
            for v in vehicles:
                if _normalize_plate(v.plate) == norm_plate:
                    return v

    return None


def _get_daily_data(session: Session, driver_id: str, vehicle: Vehicle | None,
                    license_number: str | None, current: date,
                    day_start_time: time | None = None) -> dict:
    """Gather all daily data needed for settlement calculation.

    Args:
        day_start_time: Custom start time for this day's window. Only applied
            to the first day of the range (caller controls when to pass it).
            None means midnight (00:00).
    """
    vehicle_id = vehicle.id if vehicle else None
    start_time_val = day_start_time if day_start_time else time.min

    # Driver/vehicle filter (shared by both queries)
    def _owner_filter():
        if driver_id and vehicle_id:
            return (Trip.driver_id == driver_id) | (Trip.vehicle_id == vehicle_id)
        elif driver_id:
            return Trip.driver_id == driver_id
        elif vehicle_id:
            return Trip.vehicle_id == vehicle_id
        return None

    owner_cond = _owner_filter()

    # Prima trips: naive datetimes (local time without timezone)
    prima_start = datetime.combine(current, start_time_val)
    prima_end = datetime.combine(current + timedelta(days=1), time.min)
    prima_filters = [
        Trip.started_at >= prima_start,
        Trip.started_at < prima_end,
        Trip.source == "prima",
    ]
    if owner_cond is not None:
        prima_filters.append(owner_cond)
    prima_trips = session.query(Trip).filter(*prima_filters).all()

    # FreeNow trips: timezone-aware datetimes (Europe/Madrid)
    local_start = datetime.combine(current, start_time_val, tzinfo=LOCAL_TZ)
    local_end = datetime.combine(current + timedelta(days=1), time.min, tzinfo=LOCAL_TZ)
    freenow_filters = [
        Trip.started_at >= local_start,
        Trip.started_at < local_end,
        Trip.source == "freenow",
    ]
    if owner_cond is not None:
        freenow_filters.append(owner_cond)
    freenow_trips = session.query(Trip).filter(*freenow_filters).all()

    # Prima amount
    prima_amount = sum(
        Decimal(str(t.gross_amount or 0))
        for t in prima_trips
    )

    # Incidents: prima trips with distance_km == 0 AND duration_minutes < 0.5
    # Exclude trips marked as "invalid" in PendingValidation
    invalidated_trip_ids = set(
        pv.trip_id for pv in session.query(PendingValidation.trip_id).filter(
            PendingValidation.validation_type == "incident",
            PendingValidation.status == "invalid",
            PendingValidation.trip_id.isnot(None),
        ).all()
    )
    incidents_amount = sum(
        Decimal(str(t.gross_amount or 0))
        for t in prima_trips
        if (t.distance_km is not None and float(t.distance_km) == 0)
        and (t.duration_minutes is not None and float(t.duration_minutes) < 0.5)
        and t.id not in invalidated_trip_ids
    )

    # FreeNow bruto that adds to recaudacion:
    # Only FIXED fare trips (METERED goes through taximeter/prima)
    freenow_fixed_bruto = sum(
        Decimal(str(t.gross_amount or 0))
        for t in freenow_trips
        if t.fare_type != "METERED"
    )

    # FreeNow tips (TOUR TIP) — added AFTER commission deduction
    freenow_fixed_tips = sum(
        abs(Decimal(str(t.tips or 0)))
        for t in freenow_trips
        if t.fare_type != "METERED"
    )

    # FreeNow APP-paid bruto (paid via app, not cash)
    freenow_app_paid_bruto = sum(
        Decimal(str(t.gross_amount or 0))
        for t in freenow_trips
        if t.fare_type != "METERED"
        and t.payment_method in ("APP", "tarjeta")
    )

    # FreeNow APP-paid tips
    freenow_app_tips = sum(
        abs(Decimal(str(t.tips or 0)))
        for t in freenow_trips
        if t.fare_type != "METERED"
        and t.payment_method in ("APP", "tarjeta")
    )

    # FreeNow CASH bruto (all cash trips, FIXED and METERED)
    # Used to calculate cash commission deducted from AppFN
    freenow_cash_bruto = sum(
        Decimal(str(t.gross_amount or 0))
        for t in freenow_trips
        if t.payment_method in ("CASH", "efectivo")
    )

    # Uber: query UberDailySummary by license_number (primary) or vehicle_id (fallback)
    uber_t3_fixed = Decimal("0.00")
    uber_total_payment = Decimal("0.00")
    uber_row = None
    if license_number:
        uber_row = session.query(UberDailySummary).filter(
            UberDailySummary.date == current,
            UberDailySummary.license_number == license_number,
        ).first()
    if not uber_row and vehicle_id:
        uber_row = session.query(UberDailySummary).filter(
            UberDailySummary.date == current,
            UberDailySummary.vehicle_id == vehicle_id,
        ).first()
    if uber_row:
        uber_t3_fixed = Decimal(str(uber_row.t3_fixed or 0))
        uber_total_payment = Decimal(str(uber_row.total_payment or 0))

    # TPV/VISA: query TpvDailyTotal by license_number (primary) or vehicle_id (fallback)
    tpv_visa_total = Decimal("0.00")
    if license_number:
        tpv_result = session.query(func.sum(TpvDailyTotal.amount)).filter(
            TpvDailyTotal.date == current,
            TpvDailyTotal.license_number == license_number,
        ).scalar()
        if tpv_result:
            tpv_visa_total = Decimal(str(tpv_result))
    if tpv_visa_total == 0 and vehicle_id:
        tpv_result = session.query(func.sum(TpvDailyTotal.amount)).filter(
            TpvDailyTotal.date == current,
            TpvDailyTotal.vehicle_id == vehicle_id,
        ).scalar()
        if tpv_result:
            tpv_visa_total = Decimal(str(tpv_result))

    # Fuel expenses (by vehicle_id)
    fuel_total = Decimal("0.00")
    if vehicle_id:
        fuel_result = session.query(func.sum(FuelExpense.amount)).filter(
            FuelExpense.date == current,
            FuelExpense.vehicle_id == vehicle_id,
        ).scalar()
        if fuel_result:
            fuel_total = Decimal(str(fuel_result))

    # Other expenses (by driver_id)
    other_result = session.query(func.sum(OtherExpense.amount)).filter(
        OtherExpense.date == current,
        OtherExpense.driver_id == driver_id,
    ).scalar()
    other_expenses_total = Decimal(str(other_result)) if other_result else Decimal("0.00")

    # FreeNow adjustments (otros/incentivos) by driver_id
    freenow_adj_result = session.query(func.sum(FreenowAdjustment.amount)).filter(
        FreenowAdjustment.date == current,
        FreenowAdjustment.driver_id == driver_id,
    ).scalar()
    freenow_adjustments = Decimal(str(freenow_adj_result)) if freenow_adj_result else Decimal("0.00")

    return {
        "prima_amount": prima_amount,
        "freenow_fixed_bruto": freenow_fixed_bruto,
        "freenow_fixed_tips": freenow_fixed_tips,
        "uber_t3_fixed": uber_t3_fixed,
        "incidents_amount": incidents_amount,
        "tpv_visa_total": tpv_visa_total,
        "freenow_app_paid_bruto": freenow_app_paid_bruto,
        "freenow_app_tips": freenow_app_tips,
        "freenow_cash_bruto": freenow_cash_bruto,
        "uber_total_payment": uber_total_payment,
        "fuel_total": fuel_total,
        "other_expenses_total": other_expenses_total,
        "freenow_adjustments": freenow_adjustments,
    }


def _build_driver_config(driver: Driver) -> dict:
    """Build driver config dict from Driver model."""
    return {
        "prima_base_pct": driver.prima_base_pct,
        "prima_bonus_pct": driver.prima_bonus_pct,
        "commission_threshold": driver.commission_threshold,
        "freenow_commission_driver_pct": driver.freenow_commission_driver_pct,
        "fuel_deducted_from_driver": driver.fuel_deducted_from_driver,
    }


def _calculate_range(session, driver, vehicle, license_number, sd, ed,
                     start_time: time | None = None):
    """Calculate settlements for a date range."""
    driver_config = _build_driver_config(driver)
    results = []
    current = sd
    while current <= ed:
        # Apply custom start_time only to the first day
        day_start = start_time if current == sd else None
        data = _get_daily_data(session, driver.id, vehicle, license_number,
                               current, day_start_time=day_start)
        settlement = calculate_daily_settlement(
            driver_config=driver_config,
            **data,
        )
        settlement["date"] = current
        results.append(settlement)
        current += timedelta(days=1)
    return results


TOTAL_KEYS = [
    "prima_amount", "freenow_fixed_bruto", "freenow_adjustments", "freenow_fixed", "uber_t3_fixed",
    "recaudacion_total", "incidents_amount", "recaudacion_neta",
    "tpv_visa_total", "freenow_app", "uber_total_payment", "cash",
    "iva", "parte_proporcional",
    "fuel_total", "other_expenses_total", "anticipado", "liquidacion",
]


def _calculate_totals(results: list[dict]) -> dict:
    """Sum up all numeric settlement fields."""
    totals = {}
    if results:
        for key in TOTAL_KEYS:
            totals[key] = sum(r.get(key, Decimal("0")) for r in results)
    return totals


@router.get("/liquidacion", response_class=HTMLResponse)
async def liquidacion_page(
    request: Request,
    driver_id: str = "",
    start_date: str = "",
    end_date: str = "",
    start_time: str = "00:00",
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Show settlement page with form and results."""
    drivers = session.query(Driver).filter_by(is_active=True).all()

    results = []
    driver = None
    totals = {}
    other_expenses_detail = []

    # Parse start_time (HH:MM)
    try:
        st_parts = start_time.split(":")
        start_time_obj = time(int(st_parts[0]), int(st_parts[1]))
    except (ValueError, IndexError):
        start_time_obj = time.min

    if driver_id and start_date and end_date:
        driver = session.get(Driver, driver_id)
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)

        if driver:
            license_number = _extract_license_number(driver)
            vehicle = _resolve_vehicle(session, driver)
            results = _calculate_range(session, driver, vehicle, license_number,
                                       sd, ed, start_time=start_time_obj)
            totals = _calculate_totals(results)

            # Query other expenses detail for the period
            other_expenses_detail = session.query(OtherExpense).filter(
                OtherExpense.driver_id == driver_id,
                OtherExpense.date >= sd,
                OtherExpense.date <= ed,
            ).order_by(OtherExpense.date).all()

    return templates.TemplateResponse(
        request,
        "liquidacion.html",
        {
            "user": user,
            "drivers": drivers,
            "selected_driver": driver,
            "driver_id": driver_id,
            "start_date": start_date,
            "end_date": end_date,
            "start_time": start_time,
            "results": results,
            "totals": totals,
            "other_expenses_detail": other_expenses_detail,
        },
    )




@router.post("/liquidacion/export", response_class=StreamingResponse)
async def export_liquidacion(
    request: Request,
    driver_id: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    start_time: str = Form("00:00"),
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Export settlement to Excel."""
    driver = session.get(Driver, driver_id)
    if not driver:
        return RedirectResponse(url=f"{root_path}/liquidacion", status_code=303)

    sd = date.fromisoformat(start_date)
    ed = date.fromisoformat(end_date)

    try:
        st_parts = start_time.split(":")
        start_time_obj = time(int(st_parts[0]), int(st_parts[1]))
    except (ValueError, IndexError):
        start_time_obj = time.min

    license_number = _extract_license_number(driver)
    vehicle = _resolve_vehicle(session, driver)

    results = _calculate_range(session, driver, vehicle, license_number, sd, ed,
                               start_time=start_time_obj)
    totals = _calculate_totals(results)

    buffer = export_settlement_to_excel(
        driver_name=driver.name,
        start_date=start_date,
        end_date=end_date,
        results=results,
        totals=totals,
    )

    filename = f"liquidacion_{driver.name.replace(' ', '_')}_{start_date}_{end_date}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/liquidacion/export-pdf", response_class=StreamingResponse)
async def export_liquidacion_pdf(
    request: Request,
    driver_id: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    start_time: str = Form("00:00"),
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Export settlement to PDF."""
    driver = session.get(Driver, driver_id)
    if not driver:
        return RedirectResponse(url=f"{root_path}/liquidacion", status_code=303)

    sd = date.fromisoformat(start_date)
    ed = date.fromisoformat(end_date)

    try:
        st_parts = start_time.split(":")
        start_time_obj = time(int(st_parts[0]), int(st_parts[1]))
    except (ValueError, IndexError):
        start_time_obj = time.min

    license_number = _extract_license_number(driver)
    vehicle = _resolve_vehicle(session, driver)

    results = _calculate_range(session, driver, vehicle, license_number, sd, ed,
                               start_time=start_time_obj)
    totals = _calculate_totals(results)

    buffer = export_settlement_to_pdf(
        driver_name=driver.name,
        start_date=start_date,
        end_date=end_date,
        results=results,
        totals=totals,
    )

    filename = f"liquidacion_{driver.name.replace(' ', '_')}_{start_date}_{end_date}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


