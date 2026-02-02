# src/services/trip_service.py
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.models.trip import Trip


def get_earnings_summary(session: Session, driver_id: str | None = None) -> dict:
    """Get earnings summary for dashboard."""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    start_of_month = today.replace(day=1)

    def query_total(start_date):
        q = session.query(func.coalesce(func.sum(Trip.gross_amount), 0))
        q = q.filter(func.date(Trip.started_at) >= start_date)
        if driver_id:
            q = q.filter(Trip.driver_id == driver_id)
        return float(q.scalar())

    # Daily totals for chart (last 7 days)
    labels = []
    data = []
    day_names = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(day_names[d.weekday()])
        q = session.query(func.coalesce(func.sum(Trip.gross_amount), 0))
        q = q.filter(func.date(Trip.started_at) == d)
        if driver_id:
            q = q.filter(Trip.driver_id == driver_id)
        data.append(float(q.scalar()))

    # Recent trips
    q = session.query(Trip).order_by(Trip.started_at.desc())
    if driver_id:
        q = q.filter(Trip.driver_id == driver_id)
    recent = q.limit(5).all()

    return {
        "today": query_total(today),
        "this_week": query_total(start_of_week),
        "this_month": query_total(start_of_month),
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
