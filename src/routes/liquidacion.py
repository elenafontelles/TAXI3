# src/routes/liquidacion.py
from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from src.routes.auth import require_admin
from src.database import get_session
from src.models.driver import Driver
from src.models.trip import Trip
from src.models.tpv_daily_total import TpvDailyTotal
from src.models.uber_daily_summary import UberDailySummary
from src.models.fuel_expense import FuelExpense
from src.models.other_expense import OtherExpense
from src.models.vehicle import Vehicle
from src.services.settlement_calculator import calculate_daily_settlement
from src.services.excel_exporter import export_settlement_to_excel
from src.services.pdf_exporter import export_settlement_to_pdf
from src.template_config import templates

router = APIRouter()


def _extract_license_number(driver: Driver) -> str | None:
    """Extract numeric license from driver's license_number field.

    Driver license_number format: "361 - 8921LYW" or "092 - 1234ABC"
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
                    license_number: str | None, current: date) -> dict:
    """Gather all daily data needed for settlement calculation."""
    vehicle_id = vehicle.id if vehicle else None

    # Get trips for this day (by driver_id OR vehicle_id)
    trip_filters = [func.date(Trip.started_at) == current]
    if driver_id and vehicle_id:
        trip_filters.append(
            (Trip.driver_id == driver_id) | (Trip.vehicle_id == vehicle_id)
        )
    elif driver_id:
        trip_filters.append(Trip.driver_id == driver_id)
    elif vehicle_id:
        trip_filters.append(Trip.vehicle_id == vehicle_id)

    day_trips = session.query(Trip).filter(*trip_filters).all()

    # Prima amount
    prima_amount = sum(
        Decimal(str(t.gross_amount or 0))
        for t in day_trips
        if t.source == "prima"
    )

    # Incidents: prima trips with distance_km == 0 AND duration_minutes < 0.5
    incidents_amount = sum(
        Decimal(str(t.gross_amount or 0))
        for t in day_trips
        if t.source == "prima"
        and (t.distance_km is not None and float(t.distance_km) == 0)
        and (t.duration_minutes is not None and float(t.duration_minutes) < 0.5)
    )

    # FreeNow bruto that adds to recaudacion:
    # Only FIXED fare trips (METERED goes through taximeter/prima)
    # After migration 005, fare_type is backfilled from raw_data
    # Still handle NULL fare_type (records without FARE TYPE in CSV)
    freenow_fixed_bruto = sum(
        Decimal(str(t.gross_amount or 0))
        for t in day_trips
        if t.source == "freenow" and t.fare_type != "METERED"
    )

    # FreeNow APP-paid bruto (paid via app, not cash)
    # After migration 005, payment_method is normalized to "CASH"/"APP"
    # Still handle old format ("tarjeta") for safety
    freenow_app_paid_bruto = sum(
        Decimal(str(t.gross_amount or 0))
        for t in day_trips
        if t.source == "freenow"
        and t.fare_type != "METERED"
        and t.payment_method in ("APP", "tarjeta")
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

    return {
        "prima_amount": prima_amount,
        "freenow_fixed_bruto": freenow_fixed_bruto,
        "uber_t3_fixed": uber_t3_fixed,
        "incidents_amount": incidents_amount,
        "tpv_visa_total": tpv_visa_total,
        "freenow_app_paid_bruto": freenow_app_paid_bruto,
        "uber_total_payment": uber_total_payment,
        "fuel_total": fuel_total,
        "other_expenses_total": other_expenses_total,
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


def _calculate_range(session, driver, vehicle, license_number, sd, ed):
    """Calculate settlements for a date range."""
    driver_config = _build_driver_config(driver)
    results = []
    current = sd
    while current <= ed:
        data = _get_daily_data(session, driver.id, vehicle, license_number, current)
        settlement = calculate_daily_settlement(
            driver_config=driver_config,
            **data,
        )
        settlement["date"] = current
        results.append(settlement)
        current += timedelta(days=1)
    return results


TOTAL_KEYS = [
    "prima_amount", "freenow_fixed_bruto", "uber_t3_fixed",
    "recaudacion_total", "incidents_amount", "recaudacion_neta",
    "iva", "base_imponible", "parte_proporcional",
    "tpv_visa_total", "freenow_app", "uber_total_payment",
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
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Show settlement page with form and results."""
    drivers = session.query(Driver).filter_by(is_active=True).all()

    results = []
    driver = None
    totals = {}

    if driver_id and start_date and end_date:
        driver = session.get(Driver, driver_id)
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)

        if driver:
            license_number = _extract_license_number(driver)
            vehicle = _resolve_vehicle(session, driver)
            results = _calculate_range(session, driver, vehicle, license_number, sd, ed)
            totals = _calculate_totals(results)

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
            "results": results,
            "totals": totals,
        },
    )



@router.get("/liquidacion/debug")
async def liquidacion_debug(
    session: Session = Depends(get_session),
):
    """Temporary debug endpoint — remove after investigation."""
    from fastapi.responses import JSONResponse

    target_date = date(2025, 12, 23)

    # Find Tamara
    drivers = session.query(Driver).filter_by(is_active=True).all()
    tamara = None
    for d in drivers:
        if "tamara" in d.name.lower():
            tamara = d
            break

    if not tamara:
        return JSONResponse({"error": "Tamara not found", "drivers": [d.name for d in drivers]})

    license_number = _extract_license_number(tamara)
    vehicle = _resolve_vehicle(session, tamara)
    vehicle_id = vehicle.id if vehicle else None

    # Get ALL trips for 23/12/2025 matching Tamara
    trip_filters = [func.date(Trip.started_at) == target_date]
    if tamara.id and vehicle_id:
        trip_filters.append(
            (Trip.driver_id == tamara.id) | (Trip.vehicle_id == vehicle_id)
        )
    day_trips = session.query(Trip).filter(*trip_filters).all()

    # Prima trips
    prima_trips = [t for t in day_trips if t.source == "prima"]
    # FreeNow trips
    fn_trips = [t for t in day_trips if t.source == "freenow"]
    fn_fixed = [t for t in fn_trips if t.fare_type != "METERED"]
    fn_metered = [t for t in fn_trips if t.fare_type == "METERED"]
    fn_null = [t for t in fn_trips if t.fare_type is None]

    # Also check: how many prima trips exist globally for license 361?
    all_prima = session.query(Trip).filter(Trip.source == "prima").count()
    prima_by_driver = session.query(Trip).filter(
        Trip.source == "prima", Trip.driver_id == tamara.id
    ).count()
    prima_by_vehicle = session.query(Trip).filter(
        Trip.source == "prima", Trip.vehicle_id == vehicle_id
    ).count() if vehicle_id else 0

    # Check prima date range
    from sqlalchemy import func as sqlfunc
    prima_date_range = session.query(
        sqlfunc.min(Trip.started_at), sqlfunc.max(Trip.started_at)
    ).filter(Trip.source == "prima", Trip.driver_id == tamara.id).first()

    # Sample prima trips to see their dates
    sample_prima = session.query(Trip).filter(
        Trip.source == "prima", Trip.driver_id == tamara.id
    ).order_by(Trip.started_at.desc()).limit(5).all()

    return JSONResponse({
        "driver": {"id": tamara.id, "name": tamara.name, "license": tamara.license_number},
        "vehicle": {"id": vehicle_id, "plate": vehicle.plate if vehicle else None,
                     "license": vehicle.license_number if vehicle else None},
        "license_number_extracted": license_number,
        "target_date": str(target_date),
        "total_trips_on_date": len(day_trips),
        "prima": {
            "count_on_date": len(prima_trips),
            "sum": str(sum(float(t.gross_amount or 0) for t in prima_trips)),
            "total_prima_trips_in_db": all_prima,
            "prima_by_driver_id": prima_by_driver,
            "prima_by_vehicle_id": prima_by_vehicle,
            "date_range": [str(prima_date_range[0]) if prima_date_range[0] else None,
                           str(prima_date_range[1]) if prima_date_range[1] else None],
            "recent_prima_dates": [str(t.started_at) for t in sample_prima],
        },
        "freenow": {
            "total_on_date": len(fn_trips),
            "fixed_count": len(fn_fixed),
            "fixed_sum": str(sum(float(t.gross_amount or 0) for t in fn_fixed)),
            "fixed_details": [{"amount": str(t.gross_amount), "fare_type": t.fare_type,
                               "payment": t.payment_method, "tips": str(t.tips),
                               "tolls": str(t.tolls), "commission": str(t.commission),
                               "payout": str(t.payout_amount),
                               "raw_bruto": (t.raw_data or {}).get("BRUTO"),
                               "raw_neto": (t.raw_data or {}).get("NETO"),
                               "raw_tips": (t.raw_data or {}).get("TIPS")}
                              for t in fn_fixed],
        },
    })


@router.post("/liquidacion/export", response_class=StreamingResponse)
async def export_liquidacion(
    request: Request,
    driver_id: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Export settlement to Excel."""
    from src.config import settings

    root_path = settings.root_path

    driver = session.get(Driver, driver_id)
    if not driver:
        return RedirectResponse(url=f"{root_path}/liquidacion", status_code=303)

    sd = date.fromisoformat(start_date)
    ed = date.fromisoformat(end_date)

    license_number = _extract_license_number(driver)
    vehicle = _resolve_vehicle(session, driver)

    results = _calculate_range(session, driver, vehicle, license_number, sd, ed)
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
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Export settlement to PDF."""
    from src.config import settings

    root_path = settings.root_path

    driver = session.get(Driver, driver_id)
    if not driver:
        return RedirectResponse(url=f"{root_path}/liquidacion", status_code=303)

    sd = date.fromisoformat(start_date)
    ed = date.fromisoformat(end_date)

    license_number = _extract_license_number(driver)
    vehicle = _resolve_vehicle(session, driver)

    results = _calculate_range(session, driver, vehicle, license_number, sd, ed)
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
