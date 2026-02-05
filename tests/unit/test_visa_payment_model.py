"""Tests for VisaPayment model."""
import pytest
from datetime import date, time
from decimal import Decimal
from src.models.visa_payment import VisaPayment


def test_visa_payment_creation():
    """VisaPayment can be created with required fields."""
    vp = VisaPayment(
        date=date(2026, 2, 3),
        time=time(10, 54, 42),
        terminal_id="91901157277",
        card_last4="3386",
        brand="VISA",
        amount=Decimal("28.00"),
        vehicle_id="vehicle-123",
        source_file="lacaixa_2026-02-03.xlsx",
    )
    assert vp.amount == Decimal("28.00")
    assert vp.brand == "VISA"
    assert vp.trip_id is None
    assert vp.tip_amount is None


def test_visa_payment_with_tip():
    """VisaPayment can track tip amount."""
    vp = VisaPayment(
        date=date(2026, 2, 3),
        time=time(10, 54, 42),
        terminal_id="91901157277",
        card_last4="3386",
        brand="VISA",
        amount=Decimal("30.00"),
        trip_id="trip-123",
        tip_amount=Decimal("2.00"),
        vehicle_id="vehicle-123",
        source_file="lacaixa_2026-02-03.xlsx",
    )
    assert vp.tip_amount == Decimal("2.00")
    assert vp.trip_id == "trip-123"
