# src/services/trip_matcher.py
"""Cross-platform trip matching service.

Prima is the source of truth (taximeter records every trip).
When a trip is done via FreeNow/Uber, Prima records it with amount=0.
This service links Prima trips to their FreeNow/Uber counterparts.
"""
import logging
from datetime import timedelta
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from src.models.trip import Trip

logger = logging.getLogger(__name__)

# Matching criteria
# Note: Using 65 min window to handle timezone discrepancies between platforms
# Prima stores UTC, FreeNow may have local time (UTC+1 in Spain)
TIME_WINDOW_MINUTES = 65  # Max time difference for matching
MIN_AMOUNT_THRESHOLD = 0.01  # Prima trips below this are considered "app trips"


def find_matching_app_trip(
    prima_trip: Trip,
    session: Session,
) -> Trip | None:
    """Find a FreeNow/Uber trip that matches this Prima trip.

    Matching criteria:
    - Same driver
    - Start time within ±5 minutes
    - Source is 'freenow' or 'uber'
    - Has a gross_amount > 0
    """
    time_start = prima_trip.started_at - timedelta(minutes=TIME_WINDOW_MINUTES)
    time_end = prima_trip.started_at + timedelta(minutes=TIME_WINDOW_MINUTES)

    match = (
        session.query(Trip)
        .filter(
            Trip.driver_id == prima_trip.driver_id,
            Trip.source.in_(["freenow", "uber"]),
            Trip.started_at >= time_start,
            Trip.started_at <= time_end,
            Trip.gross_amount > MIN_AMOUNT_THRESHOLD,
        )
        .order_by(
            # Prefer closest match by time
            sa.func.abs(sa.extract("epoch", Trip.started_at - prima_trip.started_at))
        )
        .first()
    )

    return match


def cross_match_trips(session: Session, driver_id: str | None = None) -> dict:
    """Link Prima trips (amount=0) to their FreeNow/Uber counterparts.

    Args:
        session: Database session
        driver_id: Optional - only process trips for this driver

    Returns:
        dict with stats: {'matched': N, 'already_linked': N, 'no_match': N}
    """
    import sqlalchemy as sa

    # Find Prima trips with amount ~0 that aren't already linked
    query = (
        session.query(Trip)
        .filter(
            Trip.source == "prima",
            Trip.gross_amount < MIN_AMOUNT_THRESHOLD,
            Trip.linked_trip_id.is_(None),
        )
        .order_by(Trip.started_at)  # Process in chronological order
    )

    if driver_id:
        query = query.filter(Trip.driver_id == driver_id)

    prima_trips = query.all()

    # Track which app trips have already been linked (1:1 matching)
    used_app_trip_ids = set()

    # Also get already-linked app trip IDs from DB
    existing_links = (
        session.query(Trip.linked_trip_id)
        .filter(Trip.linked_trip_id.isnot(None))
        .all()
    )
    used_app_trip_ids.update(link[0] for link in existing_links)

    stats = {"matched": 0, "already_linked": 0, "no_match": 0, "total": len(prima_trips)}

    for prima_trip in prima_trips:
        # Find matching app trip
        time_start = prima_trip.started_at - timedelta(minutes=TIME_WINDOW_MINUTES)
        time_end = prima_trip.started_at + timedelta(minutes=TIME_WINDOW_MINUTES)

        # Get candidates ordered by time proximity, exclude already-used trips
        candidates = (
            session.query(Trip)
            .filter(
                Trip.driver_id == prima_trip.driver_id,
                Trip.source.in_(["freenow", "uber"]),
                Trip.started_at >= time_start,
                Trip.started_at <= time_end,
                Trip.gross_amount > MIN_AMOUNT_THRESHOLD,
                ~Trip.id.in_(used_app_trip_ids) if used_app_trip_ids else True,
            )
            .order_by(
                sa.func.abs(sa.extract("epoch", Trip.started_at - prima_trip.started_at))
            )
            .all()
        )

        # Find first candidate not already used
        app_trip = None
        for candidate in candidates:
            if candidate.id not in used_app_trip_ids:
                app_trip = candidate
                break

        if app_trip:
            # Link the trips and mark app trip as used
            prima_trip.linked_trip_id = app_trip.id
            used_app_trip_ids.add(app_trip.id)
            stats["matched"] += 1
            logger.debug(
                f"Linked Prima #{prima_trip.external_id} -> "
                f"{app_trip.source} #{app_trip.external_id} ({app_trip.gross_amount}€)"
            )
        else:
            stats["no_match"] += 1
            logger.debug(
                f"No match for Prima #{prima_trip.external_id} at {prima_trip.started_at}"
            )

    session.commit()

    logger.info(
        f"Cross-match complete: {stats['matched']} linked, "
        f"{stats['no_match']} no match, {stats['total']} total"
    )

    return stats


def get_trip_with_amount(trip: Trip, session: Session) -> tuple[Trip, float]:
    """Get the effective amount for a trip.

    If it's a Prima trip with amount=0 and a linked app trip,
    return the app trip's amount.

    Returns:
        tuple: (source_trip, amount)
    """
    if trip.source == "prima" and trip.gross_amount < MIN_AMOUNT_THRESHOLD:
        if trip.linked_trip_id:
            linked = session.get(Trip, trip.linked_trip_id)
            if linked:
                return linked, float(linked.gross_amount)

    return trip, float(trip.gross_amount)


def get_unmatched_prima_trips(session: Session, driver_id: str | None = None) -> list[Trip]:
    """Get Prima trips with 0 amount that have no linked app trip.

    These are either:
    - Uber trips (if Uber data not yet imported)
    - Data entry errors
    - Legitimate 0-amount trips (rare)
    """
    query = (
        session.query(Trip)
        .filter(
            Trip.source == "prima",
            Trip.gross_amount < MIN_AMOUNT_THRESHOLD,
            Trip.linked_trip_id.is_(None),
        )
    )

    if driver_id:
        query = query.filter(Trip.driver_id == driver_id)

    return query.order_by(Trip.started_at.desc()).all()
