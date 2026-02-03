# src/services/trip_service.py
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from src.models.trip import Trip


def get_earnings_summary(session: Session, driver_id: str | None = None) -> dict:
    """Get earnings summary for dashboard."""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    start_of_month = today.replace(day=1)

    # Period totals (today / week / month) — single query with conditional SUM
    totals_q = session.query(
        func.coalesce(func.sum(case(
            (func.date(Trip.started_at) >= today, Trip.gross_amount), else_=0
        )), 0).label("today_total"),
        func.coalesce(func.sum(case(
            (func.date(Trip.started_at) >= start_of_week, Trip.gross_amount), else_=0
        )), 0).label("week_total"),
        func.coalesce(func.sum(Trip.gross_amount), 0).label("month_total"),
    ).filter(func.date(Trip.started_at) >= start_of_month)
    if driver_id:
        totals_q = totals_q.filter(Trip.driver_id == driver_id)
    totals = totals_q.one()

    # Daily chart — single GROUP BY query for last 7 days
    seven_days_ago = today - timedelta(days=6)
    daily_q = (session.query(
        func.date(Trip.started_at).label("day"),
        func.coalesce(func.sum(Trip.gross_amount), 0).label("total"),
    ).filter(func.date(Trip.started_at) >= seven_days_ago)
     .group_by(func.date(Trip.started_at)))
    if driver_id:
        daily_q = daily_q.filter(Trip.driver_id == driver_id)
    daily_totals = {row.day: float(row.total) for row in daily_q.all()}

    day_names = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    labels = []
    data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(day_names[d.weekday()])
        data.append(daily_totals.get(d, 0.0))

    # Recent trips
    recent_q = session.query(Trip).order_by(Trip.started_at.desc())
    if driver_id:
        recent_q = recent_q.filter(Trip.driver_id == driver_id)
    recent = recent_q.limit(5).all()

    return {
        "today": float(totals.today_total),
        "this_week": float(totals.week_total),
        "this_month": float(totals.month_total),
        "recent_trips": recent,
        "daily_chart": {"labels": labels, "data": data},
    }


SORTABLE_COLUMNS = {
    "started_at": Trip.started_at,
    "source": Trip.source,
    "gross_amount": Trip.gross_amount,
    "payout_amount": Trip.payout_amount,
    "driver_id": Trip.driver_id,
}


def get_trips_list(
    session: Session,
    driver_id: str | None = None,
    source: str | None = None,
    page: int = 1,
    per_page: int = 50,
    sort: str = "started_at",
    order: str = "desc",
) -> tuple[list, int]:
    """Get trips with pagination and sorting, optionally filtered.

    Returns (trips, total_count).
    """
    q = session.query(Trip)
    if driver_id:
        q = q.filter(Trip.driver_id == driver_id)
    if source:
        q = q.filter(Trip.source == source)

    col = SORTABLE_COLUMNS.get(sort, Trip.started_at)
    q = q.order_by(col.asc() if order == "asc" else col.desc())

    total = q.count()
    trips = q.offset((page - 1) * per_page).limit(per_page).all()
    return trips, total
