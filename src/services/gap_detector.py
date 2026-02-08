"""Detect sync gaps: alert if no successful sync in >3 days for any platform."""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.models.sync_log import SyncLog

logger = logging.getLogger(__name__)

GAP_THRESHOLD_DAYS = 3
MONITORED_PLATFORMS = ("freenow", "prima")


def check_sync_gaps(session: Session) -> list[dict]:
    """Check for platforms that haven't synced successfully in GAP_THRESHOLD_DAYS.

    Returns list of dicts with platform, last_sync, and days_since for each gap.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=GAP_THRESHOLD_DAYS)
    gaps = []

    for platform in MONITORED_PLATFORMS:
        last_success = (
            session.query(SyncLog)
            .filter(
                SyncLog.source == platform,
                SyncLog.status == "success",
            )
            .order_by(SyncLog.completed_at.desc())
            .first()
        )

        if not last_success or not last_success.completed_at:
            gaps.append({
                "platform": platform,
                "last_sync": None,
                "days_since": GAP_THRESHOLD_DAYS + 1,
            })
        elif last_success.completed_at < cutoff:
            days = (datetime.now(timezone.utc) - last_success.completed_at).days
            gaps.append({
                "platform": platform,
                "last_sync": last_success.completed_at.isoformat(),
                "days_since": days,
            })

    return gaps
