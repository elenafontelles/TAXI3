"""GDPR compliance: anonymize old GPS data and purge expired tokens."""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.models.trip import Trip
from src.models.platform_token import PlatformToken

logger = logging.getLogger(__name__)

GPS_RETENTION_DAYS = 90


def anonymize_old_gps(session: Session) -> int:
    """Null out GPS coordinates on trips older than GPS_RETENTION_DAYS.

    Returns number of trips anonymized.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=GPS_RETENTION_DAYS)

    count = (
        session.query(Trip)
        .filter(
            Trip.started_at < cutoff,
            # Only update rows that still have GPS data
            (Trip.origin_lat.isnot(None))
            | (Trip.origin_lng.isnot(None))
            | (Trip.dest_lat.isnot(None))
            | (Trip.dest_lng.isnot(None)),
        )
        .update(
            {
                Trip.origin_lat: None,
                Trip.origin_lng: None,
                Trip.dest_lat: None,
                Trip.dest_lng: None,
            },
            synchronize_session=False,
        )
    )

    if count:
        session.commit()
        logger.info(f"GDPR: anonymized GPS on {count} trips older than {GPS_RETENTION_DAYS} days")

    return count


def purge_expired_tokens(session: Session) -> int:
    """Delete expired or revoked PlatformToken records.

    Returns number of tokens purged.
    """
    now = datetime.now(timezone.utc)

    count = (
        session.query(PlatformToken)
        .filter(
            (PlatformToken.expires_at < now)
            | (PlatformToken.is_valid == False)
            | (PlatformToken.revoked_at.isnot(None))
        )
        .delete(synchronize_session=False)
    )

    if count:
        session.commit()
        logger.info(f"GDPR: purged {count} expired/revoked platform tokens")

    return count
