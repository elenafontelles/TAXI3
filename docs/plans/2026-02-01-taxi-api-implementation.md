# TAXI API Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a billing consolidation system for 3 taxis that scrapes trip data from Uber, FreeNow, and Prima, stores it in PostgreSQL, and serves a mobile-friendly dashboard for 5 users.

**Architecture:** FastAPI serves server-rendered HTML (Jinja2 + Bootstrap 5 + Chart.js). Playwright scrapers run via cron to download CSV data nightly. A Python parser imports CSVs into PostgreSQL. Email alerts on failure.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 15, Playwright, Jinja2, Bootstrap 5, Chart.js, Docker Compose, pytest

---

## Epic 1: Project Foundation

### Task 1: Create directory structure and initial files

**Files:**
- Create: `src/__init__.py`
- Create: `src/models/__init__.py`
- Create: `src/routes/__init__.py`
- Create: `src/services/__init__.py`
- Create: `src/templates/.gitkeep`
- Create: `src/static/.gitkeep`
- Create: `scrapers/.gitkeep`
- Create: `scripts/.gitkeep`
- Create: `migrations/.gitkeep`
- Create: `imports/.gitkeep`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/e2e/__init__.py`

**Step 1: Create all directories and init files**

```bash
mkdir -p src/models src/routes src/services src/templates src/static
mkdir -p scrapers scripts migrations imports
mkdir -p tests/unit tests/integration tests/e2e

touch src/__init__.py src/models/__init__.py src/routes/__init__.py src/services/__init__.py
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py tests/e2e/__init__.py
touch src/templates/.gitkeep src/static/.gitkeep
touch scrapers/.gitkeep scripts/.gitkeep migrations/.gitkeep imports/.gitkeep
```

**Step 2: Verify structure**

```bash
find src tests scrapers scripts migrations imports -type f | sort
```

Expected: All __init__.py and .gitkeep files listed.

**Step 3: Commit**

```bash
git add src/ tests/ scrapers/ scripts/ migrations/ imports/
git commit -m "feat: create project directory structure"
```

---

### Task 2: Create requirements.txt

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`

**Step 1: Write requirements.txt**

```txt
# Web framework
fastapi==0.115.0
uvicorn[standard]==0.32.0
jinja2==3.1.4
python-multipart==0.0.12

# Database
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Settings
pydantic==2.10.0
pydantic-settings==2.6.0

# Email
aiosmtplib==3.0.2

# Data processing
pandas==2.2.3

# Browser automation
playwright==1.49.0
```

**Step 2: Write requirements-dev.txt**

```txt
-r requirements.txt

# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
httpx==0.28.0

# Code quality
ruff==0.8.0

# Coverage
pytest-cov==6.0.0
```

**Step 3: Commit**

```bash
git add requirements.txt requirements-dev.txt
git commit -m "feat: add Python dependencies"
```

---

### Task 3: Create .env.example and config.py

**Files:**
- Create: `.env.example`
- Create: `src/config.py`
- Test: `tests/unit/test_config.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_config.py
import os
import pytest


def test_config_loads_from_env(monkeypatch):
    """Config should load all required settings from environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/taxi_api")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
    monkeypatch.setenv("ENVIRONMENT", "testing")

    from src.config import Settings
    settings = Settings()

    assert settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/taxi_api"
    assert settings.SECRET_KEY == "test-secret-key-at-least-32-chars-long!!"
    assert settings.ENVIRONMENT == "testing"


def test_config_has_defaults(monkeypatch):
    """Config should have sensible defaults for optional fields."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/taxi_api")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")

    from src.config import Settings
    settings = Settings()

    assert settings.ENVIRONMENT == "development"
    assert settings.APP_NAME == "TAXI API"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_config.py -v
```

Expected: FAIL (ModuleNotFoundError: No module named 'src.config')

**Step 3: Write .env.example**

```bash
# .env.example - Copy to .env and fill in real values

# Database
DATABASE_URL=postgresql://taxi_admin:changeme@localhost:5432/taxi_api

# Auth
SECRET_KEY=change-this-to-a-random-string-at-least-32-chars

# App
ENVIRONMENT=development
APP_NAME=TAXI API

# Email alerts
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_TO=ivan@maitsa.com

# Platform credentials (for Playwright scrapers)
UBER_EMAIL=your-uber-email
UBER_PASSWORD=your-uber-password
FREENOW_EMAIL=your-freenow-email
FREENOW_PASSWORD=your-freenow-password
PRIMA_EMAIL=your-prima-email
PRIMA_PASSWORD=your-prima-password
```

**Step 4: Write src/config.py**

```python
# src/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "TAXI API"

    # Email alerts
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_EMAIL_TO: str = ""

    # Platform credentials (Playwright scrapers)
    UBER_EMAIL: str = ""
    UBER_PASSWORD: str = ""
    FREENOW_EMAIL: str = ""
    FREENOW_PASSWORD: str = ""
    PRIMA_EMAIL: str = ""
    PRIMA_PASSWORD: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings()
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_config.py -v
```

Expected: PASS (2 passed)

**Step 6: Commit**

```bash
git add .env.example src/config.py tests/unit/test_config.py
git commit -m "feat: add application config with Pydantic Settings"
```

---

### Task 4: Create database connection

**Files:**
- Create: `src/database.py`
- Test: `tests/unit/test_database.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_database.py
def test_get_engine_returns_engine(monkeypatch):
    """get_engine should return a SQLAlchemy engine."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")

    from src.database import get_engine
    engine = get_engine()

    from sqlalchemy import Engine
    assert isinstance(engine, Engine)


def test_get_session_returns_session(monkeypatch):
    """get_session should yield a SQLAlchemy session."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")

    from src.database import get_session
    session_gen = get_session()
    session = next(session_gen)

    from sqlalchemy.orm import Session
    assert isinstance(session, Session)

    # Clean up
    session.close()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_database.py -v
```

Expected: FAIL

**Step 3: Write src/database.py**

```python
# src/database.py
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from src.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.DATABASE_URL, echo=(settings.ENVIRONMENT == "development"))


def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_database.py -v
```

Expected: PASS (2 passed)

**Step 5: Commit**

```bash
git add src/database.py tests/unit/test_database.py
git commit -m "feat: add SQLAlchemy database connection"
```

---

### Task 5: Create Dockerfile and docker-compose.yml

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Step 1: Write Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/
COPY scrapers/ /app/scrapers/
COPY scripts/ /app/scripts/
COPY migrations/ /app/migrations/

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Write docker-compose.yml**

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15-alpine
    container_name: taxi-api-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME:-taxi_api}
      POSTGRES_USER: ${DB_USER:-taxi_admin}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?Database password required}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-taxi_admin}"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    container_name: taxi-api
    restart: unless-stopped
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql://${DB_USER:-taxi_admin}:${DB_PASSWORD}@db:5432/${DB_NAME:-taxi_api}
    ports:
      - "${API_PORT:-8000}:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./src:/app/src:ro
      - ./imports:/app/imports

volumes:
  postgres_data:
```

**Step 3: Write .dockerignore**

```
.git
.env
__pycache__
*.pyc
.pytest_cache
tests/
docs/
imports/*.csv
*.md
.gitignore
```

**Step 4: Verify docker-compose config is valid**

```bash
docker compose config --quiet
```

Expected: No output (valid config). May warn about missing .env which is fine.

**Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore
git commit -m "feat: add Docker and Docker Compose configuration"
```

---

## Epic 2: Database Models

### Task 6: Create Owner model

**Files:**
- Create: `src/models/owner.py`
- Test: `tests/unit/test_models.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_models.py
"""Tests for SQLAlchemy models. Uses in-memory SQLite for speed."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_models.py::TestOwnerModel -v
```

Expected: FAIL

**Step 3: Write src/models/owner.py**

```python
# src/models/owner.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

**Step 4: Update src/models/__init__.py**

```python
# src/models/__init__.py
from src.models.owner import Owner

__all__ = ["Owner"]
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_models.py::TestOwnerModel -v
```

Expected: PASS (2 passed)

**Step 6: Commit**

```bash
git add src/models/owner.py src/models/__init__.py tests/unit/test_models.py
git commit -m "feat: add Owner model with tests"
```

---

### Task 7: Create Driver model

**Files:**
- Create: `src/models/driver.py`
- Modify: `tests/unit/test_models.py`
- Modify: `src/models/__init__.py`

**Step 1: Write the failing test**

Append to `tests/unit/test_models.py`:

```python
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_models.py::TestDriverModel -v
```

Expected: FAIL

**Step 3: Write src/models/driver.py**

```python
# src/models/driver.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("owners.id"), nullable=False)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)

    # Platform IDs
    uber_driver_id: Mapped[str | None] = mapped_column(String(100))
    freenow_driver_id: Mapped[str | None] = mapped_column(String(100))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

**Step 4: Update src/models/__init__.py**

```python
# src/models/__init__.py
from src.models.owner import Owner
from src.models.driver import Driver

__all__ = ["Owner", "Driver"]
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_models.py::TestDriverModel -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add src/models/driver.py src/models/__init__.py tests/unit/test_models.py
git commit -m "feat: add Driver model with tests"
```

---

### Task 8: Create Vehicle model

**Files:**
- Create: `src/models/vehicle.py`
- Modify: `tests/unit/test_models.py`
- Modify: `src/models/__init__.py`

**Step 1: Write the failing test**

Append to `tests/unit/test_models.py`:

```python
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_models.py::TestVehicleModel -v
```

Expected: FAIL

**Step 3: Write src/models/vehicle.py**

```python
# src/models/vehicle.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plate: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100))
    brand: Mapped[str | None] = mapped_column(String(50))
    year: Mapped[int | None] = mapped_column(Integer)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("owners.id"), nullable=False)
    taximeter_id: Mapped[str | None] = mapped_column(String(50))
    uber_vehicle_id: Mapped[str | None] = mapped_column(String(100))
    freenow_vehicle_id: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

**Step 4: Update src/models/__init__.py**

```python
# src/models/__init__.py
from src.models.owner import Owner
from src.models.driver import Driver
from src.models.vehicle import Vehicle

__all__ = ["Owner", "Driver", "Vehicle"]
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_models.py::TestVehicleModel -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add src/models/vehicle.py src/models/__init__.py tests/unit/test_models.py
git commit -m "feat: add Vehicle model with tests"
```

---

### Task 9: Create Shift model

**Files:**
- Create: `src/models/shift.py`
- Modify: `tests/unit/test_models.py`
- Modify: `src/models/__init__.py`

**Step 1: Write the failing test**

Append to `tests/unit/test_models.py`:

```python
from datetime import datetime, timezone


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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_models.py::TestShiftModel -v
```

Expected: FAIL

**Step 3: Write src/models/shift.py**

```python
# src/models/shift.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(100))

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    km_free: Mapped[float | None] = mapped_column(Numeric(10, 2))
    km_occupied: Mapped[float | None] = mapped_column(Numeric(10, 2))
    max_speed: Mapped[float | None] = mapped_column(Numeric(5, 1))
    total_earnings: Mapped[float | None] = mapped_column(Numeric(10, 2))

    raw_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

**Step 4: Update src/models/__init__.py**

```python
# src/models/__init__.py
from src.models.owner import Owner
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.models.shift import Shift

__all__ = ["Owner", "Driver", "Vehicle", "Shift"]
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_models.py::TestShiftModel -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add src/models/shift.py src/models/__init__.py tests/unit/test_models.py
git commit -m "feat: add Shift model with tests"
```

---

### Task 10: Create Trip model (core table)

**Files:**
- Create: `src/models/trip.py`
- Modify: `tests/unit/test_models.py`
- Modify: `src/models/__init__.py`

**Step 1: Write the failing test**

Append to `tests/unit/test_models.py`:

```python
class TestTripModel:
    def test_create_trip(self, db_session):
        from src.models.owner import Owner
        from src.models.driver import Driver
        from src.models.vehicle import Vehicle
        from src.models.trip import Trip

        owner = Owner(name="Ivan", tax_id="12345678A")
        db_session.add(owner)
        db_session.commit()

        driver = Driver(name="Driver 1", license_number="LIC001", owner_id=owner.id)
        vehicle = Vehicle(plate="1234ABC", license_number="T-1234", owner_id=owner.id)
        db_session.add_all([driver, vehicle])
        db_session.commit()

        trip = Trip(
            source="uber",
            external_id="uber_trip_001",
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            started_at=datetime(2026, 1, 27, 10, 30, tzinfo=timezone.utc),
            gross_amount=25.50,
            commission=5.10,
            payout_amount=20.40,
            payment_method="card",
        )
        db_session.add(trip)
        db_session.commit()

        saved = db_session.query(Trip).first()
        assert saved.source == "uber"
        assert saved.external_id == "uber_trip_001"
        assert float(saved.gross_amount) == 25.50
        assert float(saved.payout_amount) == 20.40

    def test_trip_requires_source_and_amount(self, db_session):
        from src.models.owner import Owner
        from src.models.driver import Driver
        from src.models.vehicle import Vehicle
        from src.models.trip import Trip

        owner = Owner(name="Ivan", tax_id="99999999Z")
        db_session.add(owner)
        db_session.commit()

        driver = Driver(name="D2", license_number="LIC999", owner_id=owner.id)
        vehicle = Vehicle(plate="9999ZZZ", license_number="T-9999", owner_id=owner.id)
        db_session.add_all([driver, vehicle])
        db_session.commit()

        with pytest.raises(Exception):
            trip = Trip(driver_id=driver.id, vehicle_id=vehicle.id)
            db_session.add(trip)
            db_session.commit()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_models.py::TestTripModel -v
```

Expected: FAIL

**Step 3: Write src/models/trip.py**

```python
# src/models/trip.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Identification
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(100))

    # Relations
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=False)
    shift_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("shifts.id"))

    # Time
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[float | None] = mapped_column(Numeric(10, 2))

    # Location
    origin_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    origin_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    dest_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    dest_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    origin_address: Mapped[str | None] = mapped_column(Text)
    dest_address: Mapped[str | None] = mapped_column(Text)

    # Distance
    distance_km: Mapped[float | None] = mapped_column(Numeric(10, 2))

    # Amounts
    currency_code: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    gross_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    commission: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    platform_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    taxes_vat: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tips: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tolls: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    adjustments: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    payout_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    amount_breakdown: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # Details
    payment_method: Mapped[str | None] = mapped_column(String(20))
    tariff_code: Mapped[str | None] = mapped_column(String(20))

    # Raw data
    raw_data: Mapped[dict | None] = mapped_column(JSON)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

**Step 4: Update src/models/__init__.py**

```python
# src/models/__init__.py
from src.models.owner import Owner
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.models.shift import Shift
from src.models.trip import Trip

__all__ = ["Owner", "Driver", "Vehicle", "Shift", "Trip"]
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_models.py::TestTripModel -v
```

Expected: PASS (2 passed)

**Step 6: Commit**

```bash
git add src/models/trip.py src/models/__init__.py tests/unit/test_models.py
git commit -m "feat: add Trip model (core table) with tests"
```

---

### Task 11: Create remaining models (SyncLog, FreeNowImport, DailySummary, PlatformToken, DsrRequest)

**Files:**
- Create: `src/models/sync_log.py`
- Create: `src/models/freenow_import.py`
- Create: `src/models/daily_summary.py`
- Create: `src/models/platform_token.py`
- Create: `src/models/dsr_request.py`
- Modify: `src/models/__init__.py`
- Modify: `tests/unit/test_models.py`

**Step 1: Write the failing test**

Append to `tests/unit/test_models.py`:

```python
class TestSyncLogModel:
    def test_create_sync_log(self, db_session):
        from src.models.sync_log import SyncLog

        log = SyncLog(
            source="uber",
            sync_type="full",
            status="completed",
            records_found=10,
            records_created=8,
            records_skipped=2,
            started_at=datetime(2026, 1, 27, 2, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 1, 27, 2, 5, tzinfo=timezone.utc),
            duration_seconds=300.0,
        )
        db_session.add(log)
        db_session.commit()

        saved = db_session.query(SyncLog).first()
        assert saved.source == "uber"
        assert saved.records_created == 8


class TestDailySummaryModel:
    def test_create_daily_summary(self, db_session):
        from src.models.owner import Owner
        from src.models.driver import Driver
        from src.models.vehicle import Vehicle
        from src.models.daily_summary import DailySummary
        from datetime import date

        owner = Owner(name="Ivan", tax_id="11111111A")
        db_session.add(owner)
        db_session.commit()

        driver = Driver(name="D1", license_number="LICDS01", owner_id=owner.id)
        vehicle = Vehicle(plate="DS01ABC", license_number="T-DS01", owner_id=owner.id)
        db_session.add_all([driver, vehicle])
        db_session.commit()

        summary = DailySummary(
            date=date(2026, 1, 27),
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            total_trips=15,
            total_gross=450.00,
            total_net=380.00,
        )
        db_session.add(summary)
        db_session.commit()

        saved = db_session.query(DailySummary).first()
        assert saved.total_trips == 15
        assert float(saved.total_gross) == 450.00
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_models.py::TestSyncLogModel tests/unit/test_models.py::TestDailySummaryModel -v
```

Expected: FAIL

**Step 3: Write all remaining models**

```python
# src/models/sync_log.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Numeric, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    sync_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    records_found: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[str | None] = mapped_column(Text)
    error_details: Mapped[dict | None] = mapped_column(JSON)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Numeric(10, 2))
```

```python
# src/models/freenow_import.py
import uuid
from datetime import datetime, date as date_type, timezone
from sqlalchemy import String, Integer, BigInteger, Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class FreeNowImport(Base):
    __tablename__ = "freenow_imports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    import_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    records_imported: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

```python
# src/models/daily_summary.py
import uuid
from datetime import datetime, date as date_type, timezone
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    driver_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("drivers.id"))
    vehicle_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("vehicles.id"))

    trips_uber: Mapped[int] = mapped_column(Integer, default=0)
    trips_freenow: Mapped[int] = mapped_column(Integer, default=0)
    trips_prima: Mapped[int] = mapped_column(Integer, default=0)
    trips_street: Mapped[int] = mapped_column(Integer, default=0)

    total_trips: Mapped[int] = mapped_column(Integer, default=0)
    total_km: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_gross: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_commission: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_net: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    avg_trip_value: Mapped[float | None] = mapped_column(Numeric(10, 2))
    euro_per_km: Mapped[float | None] = mapped_column(Numeric(10, 2))

    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("date", "driver_id", "vehicle_id"),)
```

```python
# src/models/platform_token.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, ARRAY, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class PlatformToken(Base):
    __tablename__ = "platform_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)

    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)

    token_type: Mapped[str] = mapped_column(String(20), default="Bearer")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    refresh_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_refreshed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("driver_id", "platform"),)
```

```python
# src/models/dsr_request.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class DsrRequest(Base):
    __tablename__ = "dsr_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(20), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)

    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(20), default="pending")

    status: Mapped[str] = mapped_column(String(20), default="received")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_data: Mapped[dict | None] = mapped_column(JSON)

    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

**Step 4: Update src/models/__init__.py**

```python
# src/models/__init__.py
from src.models.owner import Owner
from src.models.driver import Driver
from src.models.vehicle import Vehicle
from src.models.shift import Shift
from src.models.trip import Trip
from src.models.sync_log import SyncLog
from src.models.freenow_import import FreeNowImport
from src.models.daily_summary import DailySummary
from src.models.platform_token import PlatformToken
from src.models.dsr_request import DsrRequest

__all__ = [
    "Owner", "Driver", "Vehicle", "Shift", "Trip",
    "SyncLog", "FreeNowImport", "DailySummary",
    "PlatformToken", "DsrRequest",
]
```

**Step 5: Run all model tests**

```bash
pytest tests/unit/test_models.py -v
```

Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/models/ tests/unit/test_models.py
git commit -m "feat: add remaining models (SyncLog, FreeNowImport, DailySummary, PlatformToken, DsrRequest)"
```

---

## Epic 3: FastAPI App and Health Endpoint

### Task 12: Create FastAPI app with health endpoint

**Files:**
- Create: `src/main.py`
- Test: `tests/e2e/test_health.py`

**Step 1: Write the failing test**

```python
# tests/e2e/test_health.py
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
    from src.main import app
    return TestClient(app)


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_json(client):
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/e2e/test_health.py -v
```

Expected: FAIL

**Step 3: Write src/main.py**

```python
# src/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

# Static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "app": settings.APP_NAME}
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/e2e/test_health.py -v
```

Expected: PASS (2 passed)

**Step 5: Commit**

```bash
git add src/main.py tests/e2e/test_health.py
git commit -m "feat: add FastAPI app with health endpoint"
```

---

### Task 13: Create login page with JWT auth

**Files:**
- Create: `src/services/auth_service.py`
- Create: `src/routes/auth.py`
- Create: `src/templates/base.html`
- Create: `src/templates/login.html`
- Test: `tests/unit/test_auth_service.py`
- Test: `tests/e2e/test_auth.py`

**Step 1: Write the failing test for auth service**

```python
# tests/unit/test_auth_service.py
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")

from src.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_and_verify_password():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_and_decode_token():
    token = create_access_token({"sub": "user123", "role": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user123"
    assert payload["role"] == "admin"


def test_decode_invalid_token():
    result = decode_access_token("invalid.token.here")
    assert result is None
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_auth_service.py -v
```

Expected: FAIL

**Step 3: Write src/services/auth_service.py**

```python
# src/services/auth_service.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from src.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return None
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_auth_service.py -v
```

Expected: PASS (3 passed)

**Step 5: Write base.html template**

```html
<!-- src/templates/base.html -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}TAXI API{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="/static/style.css" rel="stylesheet">
</head>
<body>
    {% if user %}
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">TAXI API</a>
            <div class="navbar-nav ms-auto">
                <span class="nav-link text-light">{{ user.name }} ({{ user.role }})</span>
                <a class="nav-link" href="/logout">Salir</a>
            </div>
        </div>
    </nav>
    {% endif %}

    <main class="container mt-4">
        {% block content %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

**Step 6: Write login.html template**

```html
<!-- src/templates/login.html -->
{% extends "base.html" %}
{% block title %}Login - TAXI API{% endblock %}
{% block content %}
<div class="row justify-content-center mt-5">
    <div class="col-md-4">
        <h2 class="text-center mb-4">TAXI API</h2>
        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}
        <form method="post" action="/login">
            <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <input type="email" class="form-control" id="email" name="email" required>
            </div>
            <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">Entrar</button>
        </form>
    </div>
</div>
{% endblock %}
```

**Step 7: Write src/routes/auth.py**

```python
# src/routes/auth.py
from fastapi import APIRouter, Request, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.database import get_session
from src.services.auth_service import verify_password, create_access_token, decode_access_token
from src.models.driver import Driver

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, session: Session = Depends(get_session)):
    form = await request.form()
    email = form.get("email")
    password = form.get("password")

    driver = session.query(Driver).filter(Driver.email == email).first()
    if not driver or not verify_password(password, driver.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email o password incorrectos"})

    token = create_access_token({"sub": driver.id, "role": "admin" if driver.is_owner else "driver", "name": driver.name})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=86400)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


def get_current_user(request: Request) -> dict | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    return decode_access_token(token)
```

**Step 8: Write e2e test for auth routes**

```python
# tests/e2e/test_auth.py
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
    from src.main import app
    return TestClient(app)


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Email" in response.text
    assert "Password" in response.text


def test_unauthenticated_redirect(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in [302, 303, 307]
```

**Step 9: Register auth routes in main.py**

Update `src/main.py` to include:

```python
# src/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from src.config import get_settings
from src.routes.auth import router as auth_router, get_current_user

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "app": settings.APP_NAME}


@app.get("/")
async def home(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return {"message": f"Welcome {user['name']}"}
```

**Step 10: Create empty style.css**

```css
/* src/static/style.css */
body {
    background-color: #f8f9fa;
}
```

**Step 11: Run all tests**

```bash
pytest tests/ -v
```

Expected: ALL PASS

**Step 12: Commit**

```bash
git add src/services/auth_service.py src/routes/auth.py src/templates/ src/static/style.css src/main.py tests/
git commit -m "feat: add JWT auth with login page and templates"
```

---

### Task 14: Add password_hash to Driver model and add Alembic

**Files:**
- Modify: `src/models/driver.py` (add password_hash column)
- Create: `alembic.ini`
- Create: `migrations/env.py`

**Step 1: Add password_hash to Driver model**

Add this field to `src/models/driver.py`:

```python
    password_hash: Mapped[str | None] = mapped_column(String(255))
```

**Step 2: Initialize Alembic**

```bash
alembic init migrations
```

**Step 3: Configure migrations/env.py to use our models**

Edit `migrations/env.py` to import Base and set target_metadata:

```python
from src.database import Base
from src.models import *  # noqa: F401, F403 - ensures all models are registered
target_metadata = Base.metadata
```

**Step 4: Configure alembic.ini sqlalchemy.url**

Set `sqlalchemy.url` to use env variable (will be overridden in env.py).

**Step 5: Run tests to make sure nothing broke**

```bash
pytest tests/ -v
```

Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/models/driver.py alembic.ini migrations/
git commit -m "feat: add password_hash to Driver model, initialize Alembic"
```

---

## Epic 4: Dashboard Pages

### Task 15: Create dashboard home page with earnings

**Files:**
- Create: `src/routes/dashboard.py`
- Create: `src/services/trip_service.py`
- Create: `src/templates/dashboard.html`
- Test: `tests/e2e/test_dashboard.py`

This task creates the main dashboard showing daily/weekly/monthly earnings filtered by user role. Drivers see only their own data. Owners see all their drivers.

**Step 1: Write the failing test**

```python
# tests/e2e/test_dashboard.py
import pytest
from fastapi.testclient import TestClient
from src.services.auth_service import create_access_token


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
    from src.main import app
    return TestClient(app)


@pytest.fixture
def auth_cookie():
    token = create_access_token({"sub": "user1", "role": "admin", "name": "Ivan"})
    return {"access_token": token}


def test_dashboard_requires_auth(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303


def test_dashboard_loads_for_authenticated_user(client, auth_cookie):
    response = client.get("/", cookies=auth_cookie)
    assert response.status_code == 200
    assert "TAXI API" in response.text
```

**Step 2 through 5:** Implement `src/routes/dashboard.py` with Jinja2 template, register in main.py, run tests, commit.

The dashboard.html should show:
- Earnings cards: Today, This Week, This Month
- A bar chart (Chart.js) showing daily earnings for the current week
- Last 5 trips table

**Step 6: Commit**

```bash
git commit -m "feat: add dashboard home page with earnings display"
```

---

### Task 16: Create trips list page

**Files:**
- Create: `src/routes/trips.py`
- Create: `src/templates/trips.html`
- Test: `tests/e2e/test_trips.py`

Trips page shows a filterable, paginated table of trips. Drivers see only their trips. Owners see trips for their vehicles.

**Commit message:** `feat: add trips list page with filters`

---

### Task 17: Create summary/reports page (owners only)

**Files:**
- Create: `src/routes/summary.py`
- Create: `src/services/summary_service.py`
- Create: `src/templates/summary.html`
- Test: `tests/e2e/test_summary.py`

Summary page shows daily/monthly breakdown by driver, vehicle, and platform. Only accessible to owners and admin.

**Commit message:** `feat: add summary reports page for owners`

---

### Task 18: Create CSV/Excel export page (owners only)

**Files:**
- Create: `src/routes/export.py`
- Create: `src/templates/export.html`
- Test: `tests/e2e/test_export.py`

Export page lets owners select a date range and download a CSV or Excel file of trips for tax filing.

**Commit message:** `feat: add CSV/Excel export for tax filing`

---

### Task 19: Create CSV upload page (admin only)

**Files:**
- Create: `src/routes/upload.py`
- Create: `src/templates/upload.html`
- Test: `tests/e2e/test_upload.py`

Upload page lets admin drag-and-drop a CSV file. The file is saved to `/imports/` and parsed into the trips table. This is the manual fallback when scrapers fail.

**Commit message:** `feat: add manual CSV upload page`

---

### Task 20: Create sync status page (admin only)

**Files:**
- Create: `src/routes/sync.py`
- Create: `src/templates/sync.html`
- Test: `tests/e2e/test_sync.py`

Sync page shows the last scraper runs from `sync_logs` table and a button to manually trigger a re-run.

**Commit message:** `feat: add sync status page`

---

## Epic 5: CSV Parser and Import

### Task 21: Create CSV parser for Uber data

**Files:**
- Create: `scripts/parsers/__init__.py`
- Create: `scripts/parsers/uber_parser.py`
- Create: `tests/unit/test_uber_parser.py`
- Create: `tests/fixtures/uber_sample.csv`

**Step 1: Create a sample Uber CSV fixture**

Based on what Uber's driver dashboard exports. Create `tests/fixtures/uber_sample.csv` with realistic columns and 3 rows of test data.

**Step 2: Write the failing test**

```python
# tests/unit/test_uber_parser.py
from scripts.parsers.uber_parser import parse_uber_csv


def test_parse_uber_csv():
    trips = parse_uber_csv("tests/fixtures/uber_sample.csv")
    assert len(trips) == 3
    assert trips[0]["source"] == "uber"
    assert "gross_amount" in trips[0]
    assert "started_at" in trips[0]
```

**Step 3 through 5:** Implement parser, run tests, commit.

**Commit message:** `feat: add Uber CSV parser with tests`

---

### Task 22: Create CSV parser for FreeNow data

Same pattern as Task 21 but for FreeNow CSV format.

**Commit message:** `feat: add FreeNow CSV parser with tests`

---

### Task 23: Create CSV parser for Prima data

Same pattern as Task 21 but for Prima/Taxitronic CSV format.

**Commit message:** `feat: add Prima CSV parser with tests`

---

### Task 24: Create import_csvs.py script

**Files:**
- Create: `scripts/import_csvs.py`
- Test: `tests/integration/test_import.py`

This script scans `/imports/` for new CSV files, detects the source by filename pattern (`uber_*.csv`, `freenow_*.csv`, `prima_*.csv`), parses them with the appropriate parser, and inserts into the database. Uses ON CONFLICT to skip duplicates. Logs results to `sync_logs`.

**Commit message:** `feat: add CSV import script with duplicate detection`

---

## Epic 6: Playwright Scrapers

### Task 25: Create Uber scraper

**Files:**
- Create: `scrapers/uber_scraper.py`
- Create: `scrapers/base_scraper.py` (shared login/download logic)

The scraper:
1. Launches headless Chromium
2. Navigates to driver.uber.com
3. Logs in with credentials from .env
4. Navigates to earnings/trip history
5. Downloads yesterday's data as CSV
6. Saves to `imports/uber_YYYY-MM-DD.csv`

Note: This requires manual testing against the real Uber site. Write the scraper, but mark the test as `@pytest.mark.skip(reason="requires real Uber credentials")`.

**Commit message:** `feat: add Uber Playwright scraper`

---

### Task 26: Create FreeNow scraper

Same pattern as Task 25 for portal.free-now.com.

**Commit message:** `feat: add FreeNow Playwright scraper`

---

### Task 27: Create Prima scraper

Same pattern as Task 25 for Prima/Taxitronic cloud.

**Commit message:** `feat: add Prima Playwright scraper`

---

## Epic 7: Email Alerts and Cron

### Task 28: Create email alert utility

**Files:**
- Create: `scripts/send_email.py`
- Test: `tests/unit/test_email.py`

Simple function that sends an email using SMTP settings from .env. Used by import script and scrapers to report failures.

**Commit message:** `feat: add email alert utility`

---

### Task 29: Create cron orchestration script

**Files:**
- Create: `scripts/run_nightly.sh`
- Create: `crontab.example`

Shell script that runs all scrapers sequentially, then runs import_csvs.py. If any step fails, sends email alert. The `crontab.example` file shows how to install it.

```bash
# crontab.example
# Run nightly sync at 02:00 AM
0 2 * * * cd /app && /bin/bash scripts/run_nightly.sh >> /var/log/taxi-api-sync.log 2>&1
```

**Commit message:** `feat: add cron orchestration script`

---

## Epic 8: Seed Data and Final Integration

### Task 30: Create database seed script

**Files:**
- Create: `scripts/seed_db.py`

Script that creates the initial data:
- 2 owners (Ivan, Elena)
- 5 drivers (including Ivan and Elena as driver+owner)
- 3 vehicles
- Password hashes for all users

**Commit message:** `feat: add database seed script`

---

### Task 31: Create Alembic initial migration

**Step 1:** Generate migration from models

```bash
alembic revision --autogenerate -m "initial schema"
```

**Step 2:** Review generated migration, verify all 10 tables are present.

**Step 3:** Test migration up/down

```bash
# Start postgres
docker compose up db -d

# Run migration
alembic upgrade head

# Verify tables
docker compose exec db psql -U taxi_admin -d taxi_api -c "\dt"

# Run seed
python scripts/seed_db.py
```

**Commit message:** `feat: add initial Alembic migration`

---

### Task 32: Full integration test with Docker

**Step 1:** Build and start all services

```bash
docker compose up --build -d
```

**Step 2:** Run migration and seed inside container

```bash
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_db.py
```

**Step 3:** Verify health endpoint

```bash
curl http://localhost:8000/health
```

**Step 4:** Open browser and test login

Navigate to http://localhost:8000/login, log in with seeded credentials.

**Step 5:** Run full test suite

```bash
pytest tests/ -v --tb=short
```

**Step 6: Commit**

```bash
git commit -m "feat: complete integration - all services running"
```

---

### Task 33: Push to GitHub

```bash
git push origin main
```

---

## Summary

| Epic | Tasks | What it builds |
|------|-------|----------------|
| 1: Foundation | 1-5 | Directory structure, deps, config, database, Docker |
| 2: Models | 6-11 | All 10 SQLAlchemy models with tests |
| 3: App + Auth | 12-14 | FastAPI app, health endpoint, JWT login, Alembic |
| 4: Dashboard | 15-20 | All 7 web pages (dashboard, trips, summary, export, upload, sync) |
| 5: CSV Parser | 21-24 | Parsers for 3 platforms + import script |
| 6: Scrapers | 25-27 | Playwright scrapers for 3 platforms |
| 7: Alerts + Cron | 28-29 | Email alerts + nightly cron script |
| 8: Integration | 30-33 | Seed data, migrations, Docker test, push |
