# src/services/trip_service.py
from sqlalchemy.orm import Session


def get_earnings_summary(session: Session, driver_id: str | None = None) -> dict:
    """Get earnings summary for dashboard. Returns placeholder data for now."""
    return {
        "today": 0.00,
        "this_week": 0.00,
        "this_month": 0.00,
        "recent_trips": [],
        "daily_chart": {"labels": [], "data": []},
    }
