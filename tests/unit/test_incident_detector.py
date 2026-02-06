"""Tests for incident detection service."""
import pytest
from src.services.incident_detector import is_potential_incident, detect_incidents


def test_is_potential_incident_zero_km_short_time():
    trip = {"distance_km": 0, "duration_minutes": 0.3, "gross_amount": 2.85}
    assert is_potential_incident(trip) is True


def test_is_potential_incident_normal_trip():
    trip = {"distance_km": 5.5, "duration_minutes": 15, "gross_amount": 12.50}
    assert is_potential_incident(trip) is False


def test_is_potential_incident_zero_km_long_time():
    trip = {"distance_km": 0, "duration_minutes": 25, "gross_amount": 45.00}
    assert is_potential_incident(trip) is False


def test_detect_incidents_returns_list():
    trips = [
        {"id": "trip-1", "distance_km": 0, "duration_minutes": 0.2, "gross_amount": 0},
        {"id": "trip-2", "distance_km": 5, "duration_minutes": 10, "gross_amount": 15},
        {"id": "trip-3", "distance_km": 0, "duration_minutes": 0.4, "gross_amount": 2.85},
    ]
    incidents = detect_incidents(trips)
    assert "trip-1" in incidents
    assert "trip-2" not in incidents
    assert "trip-3" in incidents
