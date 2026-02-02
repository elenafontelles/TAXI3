"""Integration tests for CSV import script."""
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


def test_import_uber_csv(db_session, tmp_path):
    """Import Uber CSV should create trip records."""
    import shutil
    shutil.copy("tests/fixtures/uber_sample.csv", tmp_path / "uber_2026-01-27.csv")

    from scripts.import_csvs import import_csv_files
    from src.models.trip import Trip

    # Need an owner, driver, vehicle first
    from src.models.owner import Owner
    from src.models.driver import Driver
    from src.models.vehicle import Vehicle

    owner = Owner(name="Ivan", tax_id="12345678A")
    db_session.add(owner)
    db_session.commit()
    driver = Driver(name="Ivan Tintore", license_number="LIC001", owner_id=owner.id)
    vehicle = Vehicle(plate="1234ABC", license_number="T-1234", owner_id=owner.id)
    db_session.add_all([driver, vehicle])
    db_session.commit()

    result = import_csv_files(
        str(tmp_path),
        db_session,
        default_driver_id=driver.id,
        default_vehicle_id=vehicle.id,
    )
    assert result["files_processed"] >= 1
    assert result["records_created"] >= 1

    trips = db_session.query(Trip).all()
    assert len(trips) == 3


def test_import_freenow_csv(db_session, tmp_path):
    """Import FreeNow CSV should create trip records."""
    import shutil
    shutil.copy("tests/fixtures/freenow_sample.csv", tmp_path / "freenow_2026-01-27.csv")

    from scripts.import_csvs import import_csv_files
    from src.models.trip import Trip
    from src.models.owner import Owner
    from src.models.driver import Driver
    from src.models.vehicle import Vehicle

    owner = Owner(name="Ivan", tax_id="12345678A")
    db_session.add(owner)
    db_session.commit()
    driver = Driver(name="Ivan Tintore", license_number="LIC001", owner_id=owner.id)
    vehicle = Vehicle(plate="1234ABC", license_number="T-1234", owner_id=owner.id)
    db_session.add_all([driver, vehicle])
    db_session.commit()

    result = import_csv_files(
        str(tmp_path),
        db_session,
        default_driver_id=driver.id,
        default_vehicle_id=vehicle.id,
    )
    assert result["files_processed"] == 1
    assert result["records_created"] == 3

    trips = db_session.query(Trip).all()
    assert len(trips) == 3
    assert trips[0].source == "freenow"


def test_import_prima_csv(db_session, tmp_path):
    """Import Prima CSV should create shift records."""
    import shutil
    shutil.copy("tests/fixtures/prima_sample.csv", tmp_path / "prima_2026-01-27.csv")

    from scripts.import_csvs import import_csv_files
    from src.models.shift import Shift
    from src.models.owner import Owner
    from src.models.driver import Driver
    from src.models.vehicle import Vehicle

    owner = Owner(name="Ivan", tax_id="12345678A")
    db_session.add(owner)
    db_session.commit()
    driver = Driver(name="Ivan Tintore", license_number="LIC001", owner_id=owner.id)
    vehicle = Vehicle(plate="1234ABC", license_number="T-1234", owner_id=owner.id)
    db_session.add_all([driver, vehicle])
    db_session.commit()

    result = import_csv_files(
        str(tmp_path),
        db_session,
        default_driver_id=driver.id,
        default_vehicle_id=vehicle.id,
    )
    assert result["files_processed"] == 1
    assert result["records_created"] == 3

    shifts = db_session.query(Shift).all()
    assert len(shifts) == 3
    assert shifts[0].source == "prima"


def test_import_skips_duplicates(db_session, tmp_path):
    """Re-importing the same CSV should skip existing records."""
    import shutil
    shutil.copy("tests/fixtures/uber_sample.csv", tmp_path / "uber_2026-01-27.csv")

    from scripts.import_csvs import import_csv_files
    from src.models.trip import Trip
    from src.models.owner import Owner
    from src.models.driver import Driver
    from src.models.vehicle import Vehicle

    owner = Owner(name="Ivan", tax_id="12345678A")
    db_session.add(owner)
    db_session.commit()
    driver = Driver(name="Ivan Tintore", license_number="LIC001", owner_id=owner.id)
    vehicle = Vehicle(plate="1234ABC", license_number="T-1234", owner_id=owner.id)
    db_session.add_all([driver, vehicle])
    db_session.commit()

    # First import
    result1 = import_csv_files(
        str(tmp_path),
        db_session,
        default_driver_id=driver.id,
        default_vehicle_id=vehicle.id,
    )
    assert result1["records_created"] == 3
    assert result1["records_skipped"] == 0

    # Second import of same file
    result2 = import_csv_files(
        str(tmp_path),
        db_session,
        default_driver_id=driver.id,
        default_vehicle_id=vehicle.id,
    )
    assert result2["records_created"] == 0
    assert result2["records_skipped"] == 3

    trips = db_session.query(Trip).all()
    assert len(trips) == 3  # Still just 3, no duplicates


def test_import_unknown_source(db_session, tmp_path):
    """Unknown CSV filenames should be reported as errors."""
    # Create a CSV with unknown prefix
    unknown_csv = tmp_path / "random_data.csv"
    unknown_csv.write_text("col1,col2\nval1,val2\n")

    from scripts.import_csvs import import_csv_files
    from src.models.owner import Owner
    from src.models.driver import Driver
    from src.models.vehicle import Vehicle

    owner = Owner(name="Ivan", tax_id="12345678A")
    db_session.add(owner)
    db_session.commit()
    driver = Driver(name="Ivan Tintore", license_number="LIC001", owner_id=owner.id)
    vehicle = Vehicle(plate="1234ABC", license_number="T-1234", owner_id=owner.id)
    db_session.add_all([driver, vehicle])
    db_session.commit()

    result = import_csv_files(
        str(tmp_path),
        db_session,
        default_driver_id=driver.id,
        default_vehicle_id=vehicle.id,
    )
    assert result["files_processed"] == 0
    assert len(result["errors"]) >= 1


def test_detect_source():
    """Source detection should work based on filename prefix."""
    from scripts.import_csvs import detect_source
    assert detect_source("uber_2026-01-27.csv") == "uber"
    assert detect_source("freenow_export.csv") == "freenow"
    assert detect_source("prima_shift_data.csv") == "prima"
    assert detect_source("random.csv") is None
