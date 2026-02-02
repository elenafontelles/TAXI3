# src/services/summary_service.py
from sqlalchemy.orm import Session


def get_daily_summary(session: Session, driver_id: str | None = None) -> list:
    """Get summary data. Returns empty list for now."""
    return []
