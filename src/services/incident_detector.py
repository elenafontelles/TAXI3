"""Detect potential incidents (null tickets) in trip data."""
import logging

logger = logging.getLogger(__name__)


def is_potential_incident(trip: dict) -> bool:
    """Check if a trip is a potential incident (null ticket).

    Criteria: distance_km == 0 AND duration < 30 seconds (0.5 minutes)

    Args:
        trip: Trip dictionary with distance_km and duration_minutes keys

    Returns:
        True if trip matches incident criteria
    """
    distance = float(trip.get("distance_km") or 0)
    duration = float(trip.get("duration_minutes") or 0)
    if distance == 0 and duration < 0.5:
        return True
    return False


def detect_incidents(trips: list[dict]) -> list[str]:
    """Detect potential incidents from a list of trips.

    Args:
        trips: List of trip dictionaries, each with 'id', 'distance_km',
               and 'duration_minutes' keys

    Returns:
        List of trip IDs that are potential incidents
    """
    return [t["id"] for t in trips if is_potential_incident(t)]


def create_incident_validations(session, trip_ids: list[str]) -> int:
    """Check trips for incidents and create PendingValidation records.

    Args:
        session: SQLAlchemy session
        trip_ids: List of trip IDs to check

    Returns:
        Number of incidents created
    """
    if not trip_ids:
        return 0

    from src.models.trip import Trip
    from src.models.pending_validation import PendingValidation

    trips = session.query(Trip).filter(Trip.id.in_(trip_ids)).all()
    created = 0

    for trip in trips:
        if not is_potential_incident({
            "distance_km": trip.distance_km,
            "duration_minutes": trip.duration_minutes,
        }):
            continue

        # Skip if already has a pending validation
        existing = session.query(PendingValidation).filter_by(
            trip_id=trip.id, validation_type="incident"
        ).first()
        if existing:
            continue

        pv = PendingValidation(
            trip_id=trip.id,
            validation_type="incident",
            status="pending",
            details={
                "source": trip.source,
                "distance_km": float(trip.distance_km or 0),
                "duration_minutes": float(trip.duration_minutes or 0),
                "gross_amount": float(trip.gross_amount or 0),
                "started_at": trip.started_at.isoformat() if trip.started_at else None,
            },
        )
        session.add(pv)
        created += 1

    if created:
        session.commit()
        logger.info(f"Created {created} incident validations from {len(trip_ids)} trips")

    return created
