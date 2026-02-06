"""Tests for VISA payment matching service."""
import pytest
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from src.services.visa_matcher import match_visa_to_trip, calculate_tip


def test_match_visa_to_trip_exact_time():
    visa = {"date": date(2026, 2, 3), "time": time(10, 54, 42), "amount": Decimal("28.00")}
    trips = [
        {"id": "trip-1", "ended_at": datetime(2026, 2, 3, 10, 50), "gross_amount": 28.00},
        {"id": "trip-2", "ended_at": datetime(2026, 2, 3, 9, 0), "gross_amount": 28.00},
    ]
    match = match_visa_to_trip(visa, trips)
    assert match["trip_id"] == "trip-1"


def test_match_visa_to_trip_no_match():
    visa = {"date": date(2026, 2, 3), "time": time(10, 54, 42), "amount": Decimal("28.00")}
    trips = [{"id": "trip-1", "ended_at": datetime(2026, 2, 3, 8, 0), "gross_amount": 28.00}]
    match = match_visa_to_trip(visa, trips)
    assert match is None


def test_calculate_tip():
    assert calculate_tip(Decimal("30.00"), Decimal("28.00")) == Decimal("2.00")


def test_calculate_tip_no_tip():
    assert calculate_tip(Decimal("28.00"), Decimal("28.00")) == Decimal("0.00")
