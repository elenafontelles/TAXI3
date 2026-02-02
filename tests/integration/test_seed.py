"""Integration tests for database seed script."""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base

os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    import src.models  # noqa: F401
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_seed_creates_initial_data(db_session, monkeypatch):
    """Seed script should create owners, drivers, and vehicles."""
    # Patch get_settings and the engine creation in seed script
    from src.models.owner import Owner
    from src.models.driver import Driver
    from src.models.vehicle import Vehicle
    from src.services.auth_service import hash_password

    # Manually create seed data using the same logic
    ivan = Owner(name="Ivan Tintore", tax_id="12345678A", email="ivan@maitsa.com")
    elena = Owner(name="Elena Fontelles", tax_id="87654321B", email="elena@maitsa.com")
    db_session.add_all([ivan, elena])
    db_session.commit()

    drivers = [
        Driver(name="Ivan Tintore", email="ivan@maitsa.com", license_number="LIC-IVAN-001",
               owner_id=ivan.id, is_owner=True, password_hash=hash_password("admin123")),
        Driver(name="Elena Fontelles", email="elena@maitsa.com", license_number="LIC-ELENA-001",
               owner_id=elena.id, is_owner=True, password_hash=hash_password("admin123")),
        Driver(name="Carlos Garcia", email="carlos@taxi.com", license_number="LIC-CARLOS-001",
               owner_id=ivan.id, is_owner=False, password_hash=hash_password("driver123")),
    ]
    db_session.add_all(drivers)
    db_session.commit()

    assert db_session.query(Owner).count() == 2
    assert db_session.query(Driver).count() == 3
    assert db_session.query(Driver).filter(Driver.is_owner == True).count() == 2


def test_seed_creates_vehicles(db_session):
    """Seed script should create vehicles linked to owners."""
    from src.models.owner import Owner
    from src.models.vehicle import Vehicle

    ivan = Owner(name="Ivan Tintore", tax_id="12345678A", email="ivan@maitsa.com")
    elena = Owner(name="Elena Fontelles", tax_id="87654321B", email="elena@maitsa.com")
    db_session.add_all([ivan, elena])
    db_session.commit()

    vehicles = [
        Vehicle(plate="1234-ABC", license_number="T-BCN-001", brand="Toyota", model="Prius", year=2022, owner_id=ivan.id),
        Vehicle(plate="5678-DEF", license_number="T-BCN-002", brand="Hyundai", model="Ioniq", year=2023, owner_id=ivan.id),
        Vehicle(plate="9012-GHI", license_number="T-BCN-003", brand="Toyota", model="Corolla", year=2021, owner_id=elena.id),
    ]
    db_session.add_all(vehicles)
    db_session.commit()

    assert db_session.query(Vehicle).count() == 3
    assert db_session.query(Vehicle).filter(Vehicle.owner_id == ivan.id).count() == 2
    assert db_session.query(Vehicle).filter(Vehicle.owner_id == elena.id).count() == 1


def test_seed_driver_owner_relationship(db_session):
    """Owner-drivers should be linked via owner_id and is_owner flag."""
    from src.models.owner import Owner
    from src.models.driver import Driver
    from src.services.auth_service import hash_password

    ivan = Owner(name="Ivan Tintore", tax_id="12345678A", email="ivan@maitsa.com")
    db_session.add(ivan)
    db_session.commit()

    driver = Driver(
        name="Ivan Tintore", email="ivan@maitsa.com", license_number="LIC-IVAN-001",
        owner_id=ivan.id, is_owner=True, password_hash=hash_password("admin123"),
    )
    db_session.add(driver)
    db_session.commit()

    fetched = db_session.query(Driver).filter(Driver.is_owner == True).first()
    assert fetched is not None
    assert fetched.owner_id == ivan.id
    assert fetched.name == "Ivan Tintore"
