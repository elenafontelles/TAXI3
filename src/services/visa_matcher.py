"""Match VISA payments to trips by time proximity."""
from datetime import datetime, timedelta, date, time
from decimal import Decimal

MAX_TIME_DIFF_MINUTES = 10


def match_visa_to_trip(visa: dict, trips: list[dict]) -> dict | None:
    """Match VISA payment to trip within 10 minutes of trip end time.

    Args:
        visa: Dict with 'date', 'time', and 'amount' keys
        trips: List of trip dicts with 'id', 'ended_at', and 'gross_amount'

    Returns:
        Dict with 'trip_id' and 'tip_amount', or None if no match
    """
    visa_datetime = datetime.combine(visa["date"], visa["time"])
    max_diff = timedelta(minutes=MAX_TIME_DIFF_MINUTES)
    best_match = None
    best_diff = None

    for trip in trips:
        trip_end = trip.get("ended_at")
        if not trip_end:
            continue
        if isinstance(trip_end, str):
            trip_end = datetime.fromisoformat(trip_end)

        diff = abs(visa_datetime - trip_end)
        if diff <= max_diff:
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_match = trip

    if best_match:
        tip = calculate_tip(visa["amount"], Decimal(str(best_match["gross_amount"])))
        return {"trip_id": best_match["id"], "tip_amount": tip}

    return None


def calculate_tip(visa_amount: Decimal, trip_amount: Decimal) -> Decimal:
    """Calculate tip as difference between VISA payment and trip amount.

    Args:
        visa_amount: Amount charged to VISA card
        trip_amount: Trip fare amount

    Returns:
        Tip amount (non-negative)
    """
    diff = visa_amount - trip_amount
    return max(diff, Decimal("0.00"))
