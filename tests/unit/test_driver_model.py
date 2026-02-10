"""Tests for Driver model commission fields."""
import pytest
from src.models.driver import Driver


def test_driver_has_commission_fields():
    """Driver model should have commission configuration fields."""
    driver = Driver(
        name="Test Driver",
        license_number="TEST-001",
        owner_id="owner-123",
        prima_base_pct=40.0,
        prima_bonus_pct=45.0,
        commission_threshold=300.0,
        freenow_commission_driver_pct=0.0,
        uber_commission_driver_pct=50.0,
        fuel_deducted_from_driver=False,
    )
    assert driver.prima_base_pct == 40.0
    assert driver.prima_bonus_pct == 45.0
    assert driver.commission_threshold == 300.0
    assert driver.freenow_commission_driver_pct == 0.0
    assert driver.uber_commission_driver_pct == 50.0
    assert driver.fuel_deducted_from_driver is False


def test_driver_commission_defaults():
    """Driver should have sensible commission defaults defined in the model.

    Note: SQLAlchemy defaults are applied at the database level, not when
    instantiating objects in Python. This test verifies the default values
    are correctly defined in the model's column definitions.
    """
    # Get the default values from the column definitions
    prima_base_default = Driver.__table__.c.prima_base_pct.default.arg
    prima_bonus_default = Driver.__table__.c.prima_bonus_pct.default.arg
    commission_threshold_default = Driver.__table__.c.commission_threshold.default.arg
    freenow_commission_default = Driver.__table__.c.freenow_commission_driver_pct.default.arg
    uber_commission_default = Driver.__table__.c.uber_commission_driver_pct.default.arg

    assert prima_base_default == 40.0
    assert prima_bonus_default == 45.0
    assert commission_threshold_default == 300.0
    assert freenow_commission_default == 0.0
    assert uber_commission_default == 0.0
