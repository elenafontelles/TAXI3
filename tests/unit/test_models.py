"""Tests for SQLAlchemy models. Uses in-memory SQLite for speed."""
import pytest
from datetime import datetime, date, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    # Import all models so Base.metadata knows about their tables
    import src.models  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestOwnerModel:
    def test_create_owner(self, db_session):
        from src.models.owner import Owner

        owner = Owner(name="Ivan Tintore", tax_id="12345678A", email="ivan@test.com")
        db_session.add(owner)
        db_session.commit()

        saved = db_session.query(Owner).first()
        assert saved.name == "Ivan Tintore"
        assert saved.tax_id == "12345678A"
        assert saved.is_active is True

    def test_owner_requires_name(self, db_session):
        from src.models.owner import Owner

        with pytest.raises(Exception):
            owner = Owner(tax_id="12345678A")
            db_session.add(owner)
            db_session.commit()


class TestDriverModel:
    def test_create_driver(self, db_session):
        from src.models.owner import Owner
        from src.models.driver import Driver

        owner = Owner(name="Ivan Tintore", tax_id="12345678A")
        db_session.add(owner)
        db_session.commit()

        driver = Driver(
            name="Test Driver",
            email="driver@test.com",
            license_number="LIC001",
            owner_id=owner.id,
            is_owner=False,
        )
        db_session.add(driver)
        db_session.commit()

        saved = db_session.query(Driver).first()
        assert saved.name == "Test Driver"
        assert saved.owner_id == owner.id
        assert saved.is_owner is False
        assert saved.is_active is True


class TestVehicleModel:
    def test_create_vehicle(self, db_session):
        from src.models.owner import Owner
        from src.models.vehicle import Vehicle

        owner = Owner(name="Ivan Tintore", tax_id="12345678A")
        db_session.add(owner)
        db_session.commit()

        vehicle = Vehicle(
            plate="1234ABC",
            license_number="T-1234",
            brand="Toyota",
            model="Prius",
            year=2022,
            owner_id=owner.id,
        )
        db_session.add(vehicle)
        db_session.commit()

        saved = db_session.query(Vehicle).first()
        assert saved.plate == "1234ABC"
        assert saved.owner_id == owner.id
        assert saved.is_active is True


class TestShiftModel:
    def test_create_shift(self, db_session):
        from src.models.owner import Owner
        from src.models.driver import Driver
        from src.models.vehicle import Vehicle
        from src.models.shift import Shift

        owner = Owner(name="Ivan", tax_id="12345678A")
        db_session.add(owner)
        db_session.commit()

        driver = Driver(name="Driver 1", license_number="LIC001", owner_id=owner.id)
        vehicle = Vehicle(plate="1234ABC", license_number="T-1234", owner_id=owner.id)
        db_session.add_all([driver, vehicle])
        db_session.commit()

        shift = Shift(
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            source="prima",
            started_at=datetime(2026, 1, 27, 6, 0, tzinfo=timezone.utc),
            ended_at=datetime(2026, 1, 27, 14, 0, tzinfo=timezone.utc),
            km_free=50.0,
            km_occupied=120.0,
            total_earnings=350.00,
        )
        db_session.add(shift)
        db_session.commit()

        saved = db_session.query(Shift).first()
        assert saved.source == "prima"
        assert saved.km_occupied == 120.0
        assert saved.total_earnings == 350.00
