"""Tests for FuelExpense model."""
import pytest
from datetime import date
from decimal import Decimal
from src.models.fuel_expense import FuelExpense


def test_fuel_expense_creation():
    """FuelExpense can be created with required fields."""
    fe = FuelExpense(
        date=date(2026, 1, 30),
        vehicle_id="vehicle-123",
        liters=Decimal("30.82"),
        amount=Decimal("40.00"),
        provider="petroprix",
        source_file="repostajes.csv",
        payment_method="tarjeta",
    )
    assert fe.amount == Decimal("40.00")
    assert fe.provider == "petroprix"
    assert fe.driver_id is None


def test_fuel_expense_with_driver():
    """FuelExpense can be assigned to a driver."""
    fe = FuelExpense(
        date=date(2026, 1, 30),
        vehicle_id="vehicle-123",
        driver_id="driver-456",
        liters=Decimal("30.82"),
        amount=Decimal("40.00"),
        provider="repsol",
        source_file="factura.pdf",
        payment_method="tarjeta",
    )
    assert fe.driver_id == "driver-456"
