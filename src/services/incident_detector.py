"""Detect potential incidents (null tickets) in trip data."""


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
