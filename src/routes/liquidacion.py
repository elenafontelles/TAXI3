# src/routes/liquidacion.py
from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.routes.auth import require_admin
from src.database import get_session
from src.models.driver import Driver
from src.models.trip import Trip
from src.models.visa_payment import VisaPayment
from src.models.pending_validation import PendingValidation
from src.models.vehicle import Vehicle
from src.services.settlement_calculator import calculate_daily_settlement
from src.services.excel_exporter import export_settlement_to_excel
from src.services.pdf_exporter import export_settlement_to_pdf
from src.template_config import templates

router = APIRouter()


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

    # Check for pending validations
    pending_count = session.query(PendingValidation).filter_by(status="pending").count()

    results = []
    driver = None

    if driver_id and start_date and end_date:
        driver = session.get(Driver, driver_id)
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)

        # Get the vehicle for the driver (via owner relationship)
        vehicle = None
        if driver:
            vehicle = session.query(Vehicle).filter_by(
                owner_id=driver.owner_id, is_active=True
            ).first()

        # Generate daily settlements for date range
        current = sd
        while current <= ed:
            # Get trips for this day
            day_trips = session.query(Trip).filter(
                Trip.driver_id == driver_id,
                func.date(Trip.started_at) == current,
            ).all()

            prima_amount = sum(
                Decimal(str(t.gross_amount or 0))
                for t in day_trips
                if t.source == "prima"
            )
            freenow_bruto = sum(
                Decimal(str(t.gross_amount or 0))
                for t in day_trips
                if t.source == "freenow"
            )
            uber_net = sum(
                Decimal(str(t.gross_amount or 0))
                for t in day_trips
                if t.source == "uber"
            )

            # Get VISA total for the day
            visa_total = Decimal("0")
            if vehicle:
                visa_result = session.query(func.sum(VisaPayment.amount)).filter(
                    VisaPayment.date == current,
                    VisaPayment.vehicle_id == vehicle.id,
                ).scalar()
                if visa_result:
                    visa_total = Decimal(str(visa_result))

            # FreeNow/Uber app payments (from trips with payment_method="app")
            freenow_app = sum(
                Decimal(str(t.gross_amount or 0))
                for t in day_trips
                if t.source == "freenow" and t.payment_method == "app"
            )
            uber_app = sum(
                Decimal(str(t.gross_amount or 0))
                for t in day_trips
                if t.source == "uber" and t.payment_method == "app"
            )

            # Calculate commissions
            freenow_commission = freenow_bruto * Decimal("0.125")  # 12.5% FreeNow commission
            uber_commission = uber_net * Decimal("0.25")  # 25% Uber commission estimate

            # Calculate settlement
            settlement = calculate_daily_settlement(
                prima_amount=prima_amount,
                freenow_bruto=freenow_bruto,
                uber_net=uber_net,
                visa_total=visa_total,
                freenow_app_paid=freenow_app,
                uber_app_paid=uber_app,
                freenow_commission=freenow_commission,
                uber_commission=uber_commission,
                driver_config={
                    "commission_base_pct": driver.commission_base_pct,
                    "commission_bonus_pct": driver.commission_bonus_pct,
                    "commission_threshold": driver.commission_threshold,
                    "freenow_commission_driver_pct": driver.freenow_commission_driver_pct,
                    "uber_commission_driver_pct": driver.uber_commission_driver_pct,
                },
            )
            settlement["date"] = current
            settlement["has_incidents"] = any(t.id for t in day_trips)  # simplified
            results.append(settlement)

            current += timedelta(days=1)

    # Calculate totals
    totals = {}
    if results:
        for key in [
            "prima_amount",
            "freenow_net",
            "uber_net",
            "rec_total",
            "visa_total",
            "freenow_app_paid",
            "uber_app_paid",
            "vat",
            "driver_share",
            "cash",
            "debt",
        ]:
            totals[key] = sum(r.get(key, Decimal("0")) for r in results)

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
            "pending_count": pending_count,
        },
    )


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

    # Get the vehicle for the driver (via owner relationship)
    vehicle = session.query(Vehicle).filter_by(
        owner_id=driver.owner_id, is_active=True
    ).first()

    # Generate daily settlements for date range
    results = []
    current = sd
    while current <= ed:
        # Get trips for this day
        day_trips = session.query(Trip).filter(
            Trip.driver_id == driver_id,
            func.date(Trip.started_at) == current,
        ).all()

        prima_amount = sum(
            Decimal(str(t.gross_amount or 0))
            for t in day_trips
            if t.source == "prima"
        )
        freenow_bruto = sum(
            Decimal(str(t.gross_amount or 0))
            for t in day_trips
            if t.source == "freenow"
        )
        uber_net = sum(
            Decimal(str(t.gross_amount or 0))
            for t in day_trips
            if t.source == "uber"
        )

        # Get VISA total for the day
        visa_total = Decimal("0")
        if vehicle:
            visa_result = session.query(func.sum(VisaPayment.amount)).filter(
                VisaPayment.date == current,
                VisaPayment.vehicle_id == vehicle.id,
            ).scalar()
            if visa_result:
                visa_total = Decimal(str(visa_result))

        # FreeNow/Uber app payments (from trips with payment_method="app")
        freenow_app = sum(
            Decimal(str(t.gross_amount or 0))
            for t in day_trips
            if t.source == "freenow" and t.payment_method == "app"
        )
        uber_app = sum(
            Decimal(str(t.gross_amount or 0))
            for t in day_trips
            if t.source == "uber" and t.payment_method == "app"
        )

        # Calculate commissions
        freenow_commission = freenow_bruto * Decimal("0.125")  # 12.5% FreeNow commission
        uber_commission = uber_net * Decimal("0.25")  # 25% Uber commission estimate

        # Calculate settlement
        settlement = calculate_daily_settlement(
            prima_amount=prima_amount,
            freenow_bruto=freenow_bruto,
            uber_net=uber_net,
            visa_total=visa_total,
            freenow_app_paid=freenow_app,
            uber_app_paid=uber_app,
            freenow_commission=freenow_commission,
            uber_commission=uber_commission,
            driver_config={
                "commission_base_pct": driver.commission_base_pct,
                "commission_bonus_pct": driver.commission_bonus_pct,
                "commission_threshold": driver.commission_threshold,
                "freenow_commission_driver_pct": driver.freenow_commission_driver_pct,
                "uber_commission_driver_pct": driver.uber_commission_driver_pct,
            },
        )
        settlement["date"] = current
        results.append(settlement)

        current += timedelta(days=1)

    # Calculate totals
    totals = {}
    if results:
        for key in [
            "prima_amount",
            "freenow_net",
            "uber_net",
            "rec_total",
            "visa_total",
            "freenow_app_paid",
            "uber_app_paid",
            "vat",
            "driver_share",
            "cash",
            "debt",
        ]:
            totals[key] = sum(r.get(key, Decimal("0")) for r in results)

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

    vehicle = session.query(Vehicle).filter_by(
        owner_id=driver.owner_id, is_active=True
    ).first()

    results = []
    current = sd
    while current <= ed:
        day_trips = session.query(Trip).filter(
            Trip.driver_id == driver_id,
            func.date(Trip.started_at) == current,
        ).all()

        prima_amount = sum(
            Decimal(str(t.gross_amount or 0))
            for t in day_trips if t.source == "prima"
        )
        freenow_bruto = sum(
            Decimal(str(t.gross_amount or 0))
            for t in day_trips if t.source == "freenow"
        )
        uber_net = sum(
            Decimal(str(t.gross_amount or 0))
            for t in day_trips if t.source == "uber"
        )

        visa_total = Decimal("0")
        if vehicle:
            visa_result = session.query(func.sum(VisaPayment.amount)).filter(
                VisaPayment.date == current,
                VisaPayment.vehicle_id == vehicle.id,
            ).scalar()
            if visa_result:
                visa_total = Decimal(str(visa_result))

        freenow_app = sum(
            Decimal(str(t.gross_amount or 0))
            for t in day_trips if t.source == "freenow" and t.payment_method == "app"
        )
        uber_app = sum(
            Decimal(str(t.gross_amount or 0))
            for t in day_trips if t.source == "uber" and t.payment_method == "app"
        )

        freenow_commission = freenow_bruto * Decimal("0.125")
        uber_commission = uber_net * Decimal("0.25")

        settlement = calculate_daily_settlement(
            prima_amount=prima_amount,
            freenow_bruto=freenow_bruto,
            uber_net=uber_net,
            visa_total=visa_total,
            freenow_app_paid=freenow_app,
            uber_app_paid=uber_app,
            freenow_commission=freenow_commission,
            uber_commission=uber_commission,
            driver_config={
                "commission_base_pct": driver.commission_base_pct,
                "commission_bonus_pct": driver.commission_bonus_pct,
                "commission_threshold": driver.commission_threshold,
                "freenow_commission_driver_pct": driver.freenow_commission_driver_pct,
                "uber_commission_driver_pct": driver.uber_commission_driver_pct,
            },
        )
        settlement["date"] = current
        results.append(settlement)
        current += timedelta(days=1)

    totals = {}
    if results:
        for key in [
            "prima_amount", "freenow_net", "uber_net", "rec_total",
            "visa_total", "freenow_app_paid", "uber_app_paid",
            "vat", "driver_share", "cash", "debt",
        ]:
            totals[key] = sum(r.get(key, Decimal("0")) for r in results)

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
