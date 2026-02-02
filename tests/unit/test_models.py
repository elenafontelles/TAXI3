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
