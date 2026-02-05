"""Tests for OtherExpense model."""
import pytest
from datetime import date
from decimal import Decimal
from src.models.other_expense import OtherExpense


def test_other_expense_creation():
    """OtherExpense can be created with required fields."""
    oe = OtherExpense(
        date=date(2026, 1, 23),
        driver_id="driver-123",
        amount=Decimal("15.00"),
        description="Parking aeropuerto",
        category="parking",
    )
    assert oe.amount == Decimal("15.00")
    assert oe.category == "parking"
    assert oe.description == "Parking aeropuerto"


def test_other_expense_categories():
    """OtherExpense accepts valid categories."""
    for cat in ["parking", "lavado", "peaje", "otro"]:
        oe = OtherExpense(
            date=date(2026, 1, 23),
            driver_id="driver-123",
            amount=Decimal("10.00"),
            description="Test",
            category=cat,
        )
        assert oe.category == cat
