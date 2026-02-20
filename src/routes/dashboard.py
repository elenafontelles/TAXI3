# src/routes/dashboard.py
from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.routes.auth import require_auth
from src.database import get_session
from src.models.driver import Driver
from src.models.trip import Trip
from src.models.shift import Shift
from src.models.uber_daily_summary import UberDailySummary
from src.models.fuel_expense import FuelExpense
from src.services.settlement_calculator import calculate_freenow_net
from src.template_config import templates

router = APIRouter()


def _extract_license_number(driver: Driver) -> str | None:
    if not driver.license_number:
        return None
    lic = driver.license_number.strip()
    return lic.split(" - ")[0].strip() if " - " in lic else lic


def _get_driver_kpis(session: Session, driver: Driver, sd: date, ed: date) -> dict:
    """Calculate monthly KPIs for a single driver."""
    driver_id = driver.id
    lic_num = _extract_license_number(driver)

    # --- Prima trips ---
    prima_trips = session.query(Trip).filter(
        Trip.source == "prima",
        Trip.driver_id == driver_id,
        func.date(Trip.started_at) >= sd,
        func.date(Trip.started_at) <= ed,
    ).all()

    prima_amount = sum(Decimal(str(t.gross_amount or 0)) for t in prima_trips)
    prima_trip_count = len(prima_trips)
    prima_km = sum(Decimal(str(t.distance_km or 0)) for t in prima_trips)

    # Days worked from prima (unique dates)
    prima_days = set()
    for t in prima_trips:
        if t.started_at:
            prima_days.add(t.started_at.date() if hasattr(t.started_at, 'date') else t.started_at)

    # --- Shifts (for km_free) ---
    shifts = session.query(Shift).filter(
        Shift.driver_id == driver_id,
        func.date(Shift.started_at) >= sd,
        func.date(Shift.started_at) <= ed,
    ).all()
    km_free = sum(Decimal(str(s.km_free or 0)) for s in shifts)

    total_km = prima_km + km_free

    # --- FreeNow trips (FIXED only) ---
    freenow_trips = session.query(Trip).filter(
        Trip.source == "freenow",
        Trip.driver_id == driver_id,
        func.date(Trip.started_at) >= sd,
        func.date(Trip.started_at) <= ed,
        Trip.fare_type != "METERED",
    ).all()

    freenow_bruto = sum(Decimal(str(t.gross_amount or 0)) for t in freenow_trips)
    freenow_tips = sum(abs(Decimal(str(t.tips or 0))) for t in freenow_trips)
    freenow_trip_count = len(freenow_trips)

    # FreeNow T3: net or bruto depending on driver config
    fn_pct = Decimal(str(driver.freenow_commission_driver_pct or 0))
    if fn_pct > 0:
        freenow_t3 = calculate_freenow_net(freenow_bruto) + freenow_tips
    else:
        freenow_t3 = freenow_bruto + freenow_tips

    # FreeNow days
    freenow_days = set()
    for t in freenow_trips:
        if t.started_at:
            freenow_days.add(t.started_at.date() if hasattr(t.started_at, 'date') else t.started_at)

    # --- Uber ---
    uber_t3 = Decimal("0.00")
    uber_days = set()
    if lic_num:
        uber_rows = session.query(UberDailySummary).filter(
            UberDailySummary.license_number == lic_num,
            UberDailySummary.date >= sd,
            UberDailySummary.date <= ed,
        ).all()
        uber_t3 = sum(Decimal(str(u.t3_fixed or 0)) for u in uber_rows)
        uber_days = {u.date for u in uber_rows}

    # --- Totals ---
    # Total Rec = prima + freenow_bruto + uber_t3 (sin comision)
    total_rec_bruto = prima_amount + freenow_bruto + freenow_tips + uber_t3

    # Total Rec Neta = prima + freenow_t3_net + uber_t3 (con comision para todos)
    freenow_t3_net = calculate_freenow_net(freenow_bruto) + freenow_tips
    total_rec_neta = prima_amount + freenow_t3_net + uber_t3

    # Days worked (union of all platforms)
    all_days = prima_days | freenow_days | uber_days
    dias = len(all_days)

    # Trip count (prima + freenow; uber is daily summaries not individual trips)
    viajes = prima_trip_count + freenow_trip_count

    # EUR/km
    eur_per_km = (total_rec_neta / total_km) if total_km > 0 else Decimal("0.00")

    # Promedio diario
    promedio_diario = (total_rec_neta / dias) if dias > 0 else Decimal("0.00")

    # --- Fuel ---
    fuel_rows = session.query(FuelExpense).filter(
        FuelExpense.driver_id == driver_id,
        FuelExpense.date >= sd,
        FuelExpense.date <= ed,
    ).all()
    # If no fuel by driver_id, try by vehicle
    if not fuel_rows and lic_num:
        from src.models.vehicle import Vehicle
        vehicle = session.query(Vehicle).filter(
            Vehicle.license_number == lic_num, Vehicle.is_active == True
        ).first()
        if vehicle:
            fuel_rows = session.query(FuelExpense).filter(
                FuelExpense.vehicle_id == vehicle.id,
                FuelExpense.date >= sd,
                FuelExpense.date <= ed,
            ).all()

    fuel_cost = sum(Decimal(str(f.amount or 0)) for f in fuel_rows)
    fuel_liters = sum(Decimal(str(f.liters or 0)) for f in fuel_rows)
    fuel_price_per_liter = (fuel_cost / fuel_liters) if fuel_liters > 0 else Decimal("0.00")
    fuel_pct = (fuel_cost / total_rec_neta * 100) if total_rec_neta > 0 else Decimal("0.00")

    return {
        "driver_name": driver.name,
        "dias": dias,
        "viajes": viajes,
        "prima": float(prima_amount.quantize(Decimal("0.01"))),
        "freenow_t3": float(freenow_t3.quantize(Decimal("0.01"))),
        "uber_t3": float(uber_t3.quantize(Decimal("0.01"))),
        "total_rec": float(total_rec_bruto.quantize(Decimal("0.01"))),
        "total_rec_neta": float(total_rec_neta.quantize(Decimal("0.01"))),
        "km": float(total_km.quantize(Decimal("0.01"))),
        "eur_per_km": float(eur_per_km.quantize(Decimal("0.01"))),
        "promedio_diario": float(promedio_diario.quantize(Decimal("0.01"))),
        # Fuel
        "fuel_cost": float(fuel_cost.quantize(Decimal("0.01"))),
        "fuel_liters": float(fuel_liters.quantize(Decimal("0.01"))),
        "fuel_price_per_liter": float(fuel_price_per_liter.quantize(Decimal("0.01"))),
        "fuel_pct": float(fuel_pct.quantize(Decimal("0.01"))),
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: dict = Depends(require_auth),
    session: Session = Depends(get_session),
):
    today = date.today()
    start_of_month = today.replace(day=1)

    drivers = session.query(Driver).filter_by(is_active=True).order_by(Driver.name).all()

    driver_kpis = []
    for d in drivers:
        kpis = _get_driver_kpis(session, d, start_of_month, today)
        driver_kpis.append(kpis)

    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "driver_kpis": driver_kpis,
        "month_label": today.strftime("%B %Y"),
    })
