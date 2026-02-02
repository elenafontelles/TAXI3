"""Seed the database with initial data."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.database import Base
from src.models.owner import Owner
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.services.auth_service import hash_password
import src.models  # noqa: F401 - register all models


def seed():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if already seeded
        if session.query(Owner).first():
            print("Database already seeded. Skipping.")
            return

        # Owners
        ivan = Owner(name="Ivan Tintore", tax_id="12345678A", email="ivan@maitsa.com", phone="+34600000001")
        elena = Owner(name="Elena Fontelles", tax_id="87654321B", email="elena@maitsa.com", phone="+34600000002")
        session.add_all([ivan, elena])
        session.commit()
        print(f"Created owners: Ivan ({ivan.id}), Elena ({elena.id})")

        # Drivers (owners who also drive + 3 employees)
        drivers = [
            Driver(name="Ivan Tintore", email="ivan@maitsa.com", license_number="LIC-IVAN-001",
                   owner_id=ivan.id, is_owner=True, password_hash=hash_password("admin123")),
            Driver(name="Elena Fontelles", email="elena@maitsa.com", license_number="LIC-ELENA-001",
                   owner_id=elena.id, is_owner=True, password_hash=hash_password("admin123")),
            Driver(name="Carlos Garcia", email="carlos@taxi.com", license_number="LIC-CARLOS-001",
                   owner_id=ivan.id, is_owner=False, password_hash=hash_password("driver123")),
            Driver(name="Maria Lopez", email="maria@taxi.com", license_number="LIC-MARIA-001",
                   owner_id=ivan.id, is_owner=False, password_hash=hash_password("driver123")),
            Driver(name="Pedro Martinez", email="pedro@taxi.com", license_number="LIC-PEDRO-001",
                   owner_id=elena.id, is_owner=False, password_hash=hash_password("driver123")),
        ]
        session.add_all(drivers)
        session.commit()
        print(f"Created {len(drivers)} drivers")

        # Vehicles (3 taxis)
        vehicles = [
            Vehicle(plate="1234-ABC", license_number="T-BCN-001", brand="Toyota", model="Prius", year=2022, owner_id=ivan.id),
            Vehicle(plate="5678-DEF", license_number="T-BCN-002", brand="Hyundai", model="Ioniq", year=2023, owner_id=ivan.id),
            Vehicle(plate="9012-GHI", license_number="T-BCN-003", brand="Toyota", model="Corolla", year=2021, owner_id=elena.id),
        ]
        session.add_all(vehicles)
        session.commit()
        print(f"Created {len(vehicles)} vehicles")

        print("\nSeed complete!")
        print(f"  Owners: {session.query(Owner).count()}")
        print(f"  Drivers: {session.query(Driver).count()}")
        print(f"  Vehicles: {session.query(Vehicle).count()}")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
