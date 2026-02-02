# src/models/__init__.py
from src.models.owner import Owner
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.models.shift import Shift
from src.models.trip import Trip

__all__ = [
    "Owner",
    "Driver",
    "Vehicle",
    "Shift",
    "Trip",
]
