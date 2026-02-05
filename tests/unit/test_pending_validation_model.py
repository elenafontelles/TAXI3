"""Tests for PendingValidation model."""
import pytest
from src.models.pending_validation import PendingValidation


def test_pending_validation_creation():
    """PendingValidation can be created with required fields."""
    pv = PendingValidation(
        trip_id="trip-123",
        validation_type="incident",
        status="pending",
        details={"reason": "0km trip"},
    )
    assert pv.validation_type == "incident"
    assert pv.status == "pending"
    assert pv.details["reason"] == "0km trip"
    assert pv.resolved_at is None
    assert pv.resolved_by is None


def test_pending_validation_types():
    """Validation type should accept valid values."""
    for vtype in ["incident", "visa_no_match", "fuel_no_match"]:
        pv = PendingValidation(
            validation_type=vtype,
            status="pending",
        )
        assert pv.validation_type == vtype
