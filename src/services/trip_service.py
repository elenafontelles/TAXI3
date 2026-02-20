# src/services/trip_service.py
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func, case, extract, cast, Date
from sqlalchemy.orm import Session
from src.models.trip import Trip
from src.models.driver import Driver


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


def get_advanced_analytics(session: Session, driver_id: str | None = None) -> dict:
    """Get advanced analytics: EUR/km per platform, EUR/hour per time slot, driver comparison."""
    start_of_month = date.today().replace(day=1)

    base_filter = [cast(Trip.started_at, Date) >= start_of_month]
    if driver_id:
        base_filter.append(Trip.driver_id == driver_id)

    # EUR/km per platform (this month)
    platform_q = (
        session.query(
            Trip.source,
            func.count(Trip.id).label("trips"),
            func.coalesce(func.sum(Trip.gross_amount), 0).label("gross"),
            func.coalesce(func.sum(Trip.distance_km), 0).label("km"),
            func.coalesce(func.sum(Trip.duration_minutes), 0).label("minutes"),
        )
        .filter(*base_filter)
        .group_by(Trip.source)
    )

    platform_stats = {}
    for row in platform_q.all():
        km = float(row.km) if row.km else 0
        mins = float(row.minutes) if row.minutes else 0
        gross = float(row.gross)
        platform_stats[row.source] = {
            "trips": row.trips,
            "gross": round(gross, 2),
            "km": round(km, 1),
            "hours": round(mins / 60, 1),
            "eur_per_km": round(gross / km, 2) if km > 0 else 0,
            "eur_per_hour": round(gross / (mins / 60), 2) if mins > 0 else 0,
        }

    # EUR/hour per time slot (2-hour blocks)
    hourly_q = (
        session.query(
            extract("hour", Trip.started_at).label("hour"),
            func.count(Trip.id).label("trips"),
            func.coalesce(func.sum(Trip.gross_amount), 0).label("gross"),
        )
        .filter(*base_filter)
        .group_by(extract("hour", Trip.started_at))
        .order_by(extract("hour", Trip.started_at))
    )

    hourly_raw = {int(r.hour): {"trips": r.trips, "gross": float(r.gross)} for r in hourly_q.all()}

    # Aggregate into 2-hour blocks
    time_slots = []
    for start_h in range(0, 24, 2):
        end_h = start_h + 2
        trips = sum(hourly_raw.get(h, {}).get("trips", 0) for h in range(start_h, end_h))
        gross = sum(hourly_raw.get(h, {}).get("gross", 0) for h in range(start_h, end_h))
        label = f"{start_h:02d}-{end_h:02d}"
        time_slots.append({
            "label": label,
            "trips": trips,
            "gross": round(gross, 2),
            "avg_per_trip": round(gross / trips, 2) if trips > 0 else 0,
        })

    # Driver comparison (admin only, this month)
    driver_comparison = []
    if not driver_id:
        driver_q = (
            session.query(
                Trip.driver_id,
                func.count(Trip.id).label("trips"),
                func.coalesce(func.sum(Trip.gross_amount), 0).label("gross"),
                func.coalesce(func.sum(Trip.distance_km), 0).label("km"),
            )
            .filter(cast(Trip.started_at, Date) >= start_of_month)
            .group_by(Trip.driver_id)
        )
        drivers_map = {d.id: d.name for d in session.query(Driver).all()}
        for row in driver_q.all():
            km = float(row.km) if row.km else 0
            driver_comparison.append({
                "driver_id": row.driver_id,
                "driver_name": drivers_map.get(row.driver_id, "?"),
                "trips": row.trips,
                "gross": round(float(row.gross), 2),
                "km": round(km, 1),
                "eur_per_km": round(float(row.gross) / km, 2) if km > 0 else 0,
            })
        driver_comparison.sort(key=lambda x: x["gross"], reverse=True)

    return {
        "platform_stats": platform_stats,
        "time_slots": time_slots,
        "driver_comparison": driver_comparison,
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
    start_date: date | None = None,
    end_date: date | None = None,
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
    if start_date:
        q = q.filter(func.date(Trip.started_at) >= start_date)
    if end_date:
        q = q.filter(func.date(Trip.started_at) <= end_date)

    col = SORTABLE_COLUMNS.get(sort, Trip.started_at)
    q = q.order_by(col.asc() if order == "asc" else col.desc())

    total = q.count()
    trips = q.offset((page - 1) * per_page).limit(per_page).all()
    return trips, total
