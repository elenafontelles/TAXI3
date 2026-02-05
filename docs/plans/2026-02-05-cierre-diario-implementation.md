# Sistema de Cierre Diario - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a settlement system that calculates driver payouts from multiple data sources (Prima, FreeNow, Uber, VISA, fuel) with configurable commission rules per driver.

**Architecture:** Extend existing models (Driver) with commission fields. Add new tables for VISA payments, fuel expenses, and pending validations. Create parsers for La Caixa XLSX, Petroprix CSV, Repsol PDF. Build settlement calculation service and UI pages for validation queue and settlement view.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Jinja2 templates, openpyxl (Excel), pdfplumber (PDF), pytest

**Design Document:** `docs/plans/2026-02-05-cierre-diario-design.md`

---

## Phase 1: Database Models

### Task 1: Add commission fields to Driver model

**Files:**
- Modify: `src/models/driver.py`
- Test: `tests/unit/test_driver_model.py`

**Step 1: Write the failing test**

Create `tests/unit/test_driver_model.py`:

```python
"""Tests for Driver model commission fields."""
import pytest
from src.models.driver import Driver


def test_driver_has_commission_fields():
    """Driver model should have commission configuration fields."""
    driver = Driver(
        name="Test Driver",
        license_number="TEST-001",
        owner_id="owner-123",
        commission_base_pct=40.0,
        commission_bonus_pct=45.0,
        commission_threshold=300.0,
        freenow_commission_driver_pct=0.0,
        uber_commission_driver_pct=50.0,
    )
    assert driver.commission_base_pct == 40.0
    assert driver.commission_bonus_pct == 45.0
    assert driver.commission_threshold == 300.0
    assert driver.freenow_commission_driver_pct == 0.0
    assert driver.uber_commission_driver_pct == 50.0


def test_driver_commission_defaults():
    """Driver should have sensible commission defaults."""
    driver = Driver(
        name="Test Driver",
        license_number="TEST-002",
        owner_id="owner-123",
    )
    assert driver.commission_base_pct == 40.0
    assert driver.commission_bonus_pct == 45.0
    assert driver.commission_threshold == 300.0
    assert driver.freenow_commission_driver_pct == 0.0
    assert driver.uber_commission_driver_pct == 0.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_driver_model.py -v`
Expected: FAIL with "unexpected keyword argument 'commission_base_pct'"

**Step 3: Write minimal implementation**

Modify `src/models/driver.py`, add after `updated_at`:

```python
    # Commission configuration
    commission_base_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=40.0)
    commission_bonus_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=45.0)
    commission_threshold: Mapped[float] = mapped_column(Numeric(10, 2), default=300.0)
    freenow_commission_driver_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    uber_commission_driver_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
```

Add import at top: `from sqlalchemy import String, Boolean, DateTime, ForeignKey, Numeric`

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_driver_model.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/models/driver.py tests/unit/test_driver_model.py
git commit -m "feat(models): add commission fields to Driver"
```

---

### Task 2: Create PendingValidation model

**Files:**
- Create: `src/models/pending_validation.py`
- Modify: `src/models/__init__.py`
- Test: `tests/unit/test_pending_validation_model.py`

**Step 1: Write the failing test**

Create `tests/unit/test_pending_validation_model.py`:

```python
"""Tests for PendingValidation model."""
import pytest
from datetime import datetime, timezone
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_pending_validation_model.py -v`
Expected: FAIL with "No module named 'src.models.pending_validation'"

**Step 3: Write minimal implementation**

Create `src/models/pending_validation.py`:

```python
# src/models/pending_validation.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class PendingValidation(Base):
    __tablename__ = "pending_validations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("trips.id"), nullable=True)
    validation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # incident, visa_no_match, fuel_no_match
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, valid, invalid
    details: Mapped[dict | None] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
```

Add to `src/models/__init__.py`:

```python
from src.models.pending_validation import PendingValidation
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_pending_validation_model.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/models/pending_validation.py src/models/__init__.py tests/unit/test_pending_validation_model.py
git commit -m "feat(models): add PendingValidation model"
```

---

### Task 3: Create VisaPayment model

**Files:**
- Create: `src/models/visa_payment.py`
- Modify: `src/models/__init__.py`
- Test: `tests/unit/test_visa_payment_model.py`

**Step 1: Write the failing test**

Create `tests/unit/test_visa_payment_model.py`:

```python
"""Tests for VisaPayment model."""
import pytest
from datetime import date, time
from decimal import Decimal
from src.models.visa_payment import VisaPayment


def test_visa_payment_creation():
    """VisaPayment can be created with required fields."""
    vp = VisaPayment(
        date=date(2026, 2, 3),
        time=time(10, 54, 42),
        terminal_id="91901157277",
        card_last4="3386",
        brand="VISA",
        amount=Decimal("28.00"),
        vehicle_id="vehicle-123",
        source_file="lacaixa_2026-02-03.xlsx",
    )
    assert vp.amount == Decimal("28.00")
    assert vp.brand == "VISA"
    assert vp.trip_id is None
    assert vp.tip_amount is None


def test_visa_payment_with_tip():
    """VisaPayment can track tip amount."""
    vp = VisaPayment(
        date=date(2026, 2, 3),
        time=time(10, 54, 42),
        terminal_id="91901157277",
        card_last4="3386",
        brand="VISA",
        amount=Decimal("30.00"),
        trip_id="trip-123",
        tip_amount=Decimal("2.00"),
        vehicle_id="vehicle-123",
        source_file="lacaixa_2026-02-03.xlsx",
    )
    assert vp.tip_amount == Decimal("2.00")
    assert vp.trip_id == "trip-123"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_visa_payment_model.py -v`
Expected: FAIL with "No module named 'src.models.visa_payment'"

**Step 3: Write minimal implementation**

Create `src/models/visa_payment.py`:

```python
# src/models/visa_payment.py
import uuid
from datetime import datetime, date, time, timezone
from decimal import Decimal
from sqlalchemy import String, Date, Time, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class VisaPayment(Base):
    __tablename__ = "visa_payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    terminal_id: Mapped[str] = mapped_column(String(50), nullable=False)
    card_last4: Mapped[str] = mapped_column(String(20), nullable=False)
    brand: Mapped[str] = mapped_column(String(20), nullable=False)  # VISA, MASTERCARD
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    trip_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("trips.id"), nullable=True)
    tip_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

Add to `src/models/__init__.py`:

```python
from src.models.visa_payment import VisaPayment
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_visa_payment_model.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/models/visa_payment.py src/models/__init__.py tests/unit/test_visa_payment_model.py
git commit -m "feat(models): add VisaPayment model"
```

---

### Task 4: Create FuelExpense model

**Files:**
- Create: `src/models/fuel_expense.py`
- Modify: `src/models/__init__.py`
- Test: `tests/unit/test_fuel_expense_model.py`

**Step 1: Write the failing test**

Create `tests/unit/test_fuel_expense_model.py`:

```python
"""Tests for FuelExpense model."""
import pytest
from datetime import date
from decimal import Decimal
from src.models.fuel_expense import FuelExpense


def test_fuel_expense_creation():
    """FuelExpense can be created with required fields."""
    fe = FuelExpense(
        date=date(2026, 1, 30),
        vehicle_id="vehicle-123",
        liters=Decimal("30.82"),
        amount=Decimal("40.00"),
        provider="petroprix",
        source_file="repostajes.csv",
        payment_method="tarjeta",
    )
    assert fe.amount == Decimal("40.00")
    assert fe.provider == "petroprix"
    assert fe.driver_id is None


def test_fuel_expense_with_driver():
    """FuelExpense can be assigned to a driver."""
    fe = FuelExpense(
        date=date(2026, 1, 30),
        vehicle_id="vehicle-123",
        driver_id="driver-456",
        liters=Decimal("30.82"),
        amount=Decimal("40.00"),
        provider="repsol",
        source_file="factura.pdf",
        payment_method="tarjeta",
    )
    assert fe.driver_id == "driver-456"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_fuel_expense_model.py -v`
Expected: FAIL with "No module named 'src.models.fuel_expense'"

**Step 3: Write minimal implementation**

Create `src/models/fuel_expense.py`:

```python
# src/models/fuel_expense.py
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class FuelExpense(Base):
    __tablename__ = "fuel_expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=False)
    driver_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=True)
    liters: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # petroprix, repsol
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)  # efectivo, tarjeta
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

Add to `src/models/__init__.py`:

```python
from src.models.fuel_expense import FuelExpense
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_fuel_expense_model.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/models/fuel_expense.py src/models/__init__.py tests/unit/test_fuel_expense_model.py
git commit -m "feat(models): add FuelExpense model"
```

---

### Task 5: Create OtherExpense model

**Files:**
- Create: `src/models/other_expense.py`
- Modify: `src/models/__init__.py`
- Test: `tests/unit/test_other_expense_model.py`

**Step 1: Write the failing test**

Create `tests/unit/test_other_expense_model.py`:

```python
"""Tests for OtherExpense model."""
import pytest
from datetime import date
from decimal import Decimal
from src.models.other_expense import OtherExpense


def test_other_expense_creation():
    """OtherExpense can be created with required fields."""
    oe = OtherExpense(
        date=date(2026, 1, 23),
        driver_id="driver-123",
        amount=Decimal("15.00"),
        description="Parking aeropuerto",
        category="parking",
    )
    assert oe.amount == Decimal("15.00")
    assert oe.category == "parking"
    assert oe.description == "Parking aeropuerto"


def test_other_expense_categories():
    """OtherExpense accepts valid categories."""
    for cat in ["parking", "lavado", "peaje", "otro"]:
        oe = OtherExpense(
            date=date(2026, 1, 23),
            driver_id="driver-123",
            amount=Decimal("10.00"),
            description="Test",
            category=cat,
        )
        assert oe.category == cat
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_other_expense_model.py -v`
Expected: FAIL with "No module named 'src.models.other_expense'"

**Step 3: Write minimal implementation**

Create `src/models/other_expense.py`:

```python
# src/models/other_expense.py
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class OtherExpense(Base):
    __tablename__ = "other_expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)  # parking, lavado, peaje, otro
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

Add to `src/models/__init__.py`:

```python
from src.models.other_expense import OtherExpense
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_other_expense_model.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/models/other_expense.py src/models/__init__.py tests/unit/test_other_expense_model.py
git commit -m "feat(models): add OtherExpense model"
```

---

### Task 6: Create database migration

**Files:**
- Create: `alembic/versions/XXXX_add_settlement_tables.py` (auto-generated)

**Step 1: Generate migration**

Run:
```bash
alembic revision --autogenerate -m "add settlement tables and driver commission fields"
```

**Step 2: Review the generated migration**

Check the generated file in `alembic/versions/`. It should include:
- ALTER TABLE drivers ADD commission_base_pct, commission_bonus_pct, etc.
- CREATE TABLE pending_validations
- CREATE TABLE visa_payments
- CREATE TABLE fuel_expenses
- CREATE TABLE other_expenses

**Step 3: Apply migration locally**

Run: `alembic upgrade head`
Expected: Migration applies successfully

**Step 4: Verify tables exist**

Run:
```bash
docker compose exec db psql -U taxi_admin -d taxi_api -c "\dt"
```
Expected: New tables listed

**Step 5: Commit**

```bash
git add alembic/versions/
git commit -m "chore(db): add migration for settlement tables"
```

---

## Phase 2: Parsers

### Task 7: Create La Caixa VISA parser

**Files:**
- Create: `scripts/parsers/lacaixa_parser.py`
- Test: `tests/unit/test_lacaixa_parser.py`
- Test fixture: `tests/fixtures/lacaixa_sample.xlsx`

**Step 1: Create test fixture**

Copy the sample La Caixa file to `tests/fixtures/lacaixa_sample.xlsx` (use the existing `351269212 01157277 2026-02-03.xlsx`).

**Step 2: Write the failing test**

Create `tests/unit/test_lacaixa_parser.py`:

```python
"""Tests for La Caixa VISA parser."""
import pytest
from datetime import date, time
from decimal import Decimal
from scripts.parsers.lacaixa_parser import parse_lacaixa_xlsx, detect_lacaixa_file


def test_detect_lacaixa_file():
    """Should detect La Caixa file by content."""
    assert detect_lacaixa_file("tests/fixtures/lacaixa_sample.xlsx") is True
    assert detect_lacaixa_file("tests/fixtures/prima_sample.csv") is False


def test_parse_lacaixa_xlsx():
    """Should parse La Caixa XLSX into VisaPayment dicts."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")

    assert len(records) >= 1

    first = records[0]
    assert "date" in first
    assert "time" in first
    assert "terminal_id" in first
    assert "card_last4" in first
    assert "brand" in first
    assert "amount" in first
    assert first["brand"] in ("VISA", "MASTERCARD")
    assert isinstance(first["amount"], Decimal)


def test_parse_lacaixa_extracts_license():
    """Should extract taxi license from header."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    # File header: "351269212 TAXI LIC. 1061"
    assert records[0].get("_license") == "1061"
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/test_lacaixa_parser.py -v`
Expected: FAIL with "No module named 'scripts.parsers.lacaixa_parser'"

**Step 4: Write minimal implementation**

Create `scripts/parsers/lacaixa_parser.py`:

```python
"""Parse La Caixa VISA Excel export into normalized payment dicts."""
import re
from datetime import datetime
from decimal import Decimal
from openpyxl import load_workbook


def detect_lacaixa_file(filepath: str) -> bool:
    """Detect if file is a La Caixa VISA export."""
    if not filepath.endswith(".xlsx"):
        return False
    try:
        wb = load_workbook(filepath, read_only=True, data_only=True)
        sheet = wb.active
        first_cell = sheet.cell(1, 1).value
        wb.close()
        return first_cell and "Llistat d'operacions" in str(first_cell)
    except Exception:
        return False


def parse_lacaixa_xlsx(filepath: str) -> list[dict]:
    """Parse La Caixa VISA Excel export.

    Format:
    - Row 1: "Llistat d'operacions"
    - Row 3: Account info with license (e.g., "351269212 TAXI LIC. 1061")
    - Row 5: Headers
    - Row 6+: Data rows
    """
    wb = load_workbook(filepath, read_only=True, data_only=True)
    sheet = wb.active

    # Extract license from row 3
    license_row = str(sheet.cell(3, 1).value or "")
    license_match = re.search(r"LIC\.?\s*(\d+)", license_row, re.IGNORECASE)
    license_num = license_match.group(1) if license_match else None

    records = []
    for row_idx, row in enumerate(sheet.iter_rows(min_row=6, values_only=True), start=6):
        if not row[0]:  # Skip empty rows
            continue

        # Parse datetime (format: "2026-02-03T10:54:42.618")
        dt_str = str(row[0])
        try:
            dt = datetime.fromisoformat(dt_str.split(".")[0])
        except ValueError:
            continue

        # Parse amount (format: "28,00 EUR")
        amount_str = str(row[5] or "0").replace(" EUR", "").replace(",", ".")
        try:
            amount = Decimal(amount_str)
        except Exception:
            continue

        # Extract card last 4 (format: "************3386")
        card_full = str(row[2] or "")
        card_last4 = card_full[-4:] if len(card_full) >= 4 else card_full

        records.append({
            "date": dt.date(),
            "time": dt.time(),
            "terminal_id": str(row[1] or ""),
            "card_last4": card_last4,
            "brand": str(row[3] or "VISA"),
            "amount": amount,
            "status": str(row[6] or ""),
            "_license": license_num,
        })

    wb.close()
    return records
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_lacaixa_parser.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add scripts/parsers/lacaixa_parser.py tests/unit/test_lacaixa_parser.py tests/fixtures/lacaixa_sample.xlsx
git commit -m "feat(parsers): add La Caixa VISA parser"
```

---

### Task 8: Create Petroprix CSV parser

**Files:**
- Create: `scripts/parsers/petroprix_parser.py`
- Test: `tests/unit/test_petroprix_parser.py`
- Test fixture: Copy `repostajes.csv` to `tests/fixtures/petroprix_sample.csv`

**Step 1: Write the failing test**

Create `tests/unit/test_petroprix_parser.py`:

```python
"""Tests for Petroprix fuel CSV parser."""
import pytest
from datetime import date
from decimal import Decimal
from scripts.parsers.petroprix_parser import parse_petroprix_csv, detect_petroprix_file


def test_detect_petroprix_file():
    """Should detect Petroprix CSV by columns."""
    assert detect_petroprix_file("tests/fixtures/petroprix_sample.csv") is True
    assert detect_petroprix_file("tests/fixtures/prima_sample.csv") is False


def test_parse_petroprix_csv():
    """Should parse Petroprix CSV into FuelExpense dicts."""
    records = parse_petroprix_csv("tests/fixtures/petroprix_sample.csv")

    assert len(records) >= 1

    first = records[0]
    assert "date" in first
    assert "liters" in first
    assert "amount" in first
    assert "_plate" in first
    assert "payment_method" in first
    assert first["provider"] == "petroprix"


def test_parse_petroprix_payment_methods():
    """Should map payment methods correctly."""
    records = parse_petroprix_csv("tests/fixtures/petroprix_sample.csv")
    for r in records:
        assert r["payment_method"] in ("efectivo", "tarjeta")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_petroprix_parser.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `scripts/parsers/petroprix_parser.py`:

```python
"""Parse Petroprix fuel CSV export into normalized expense dicts."""
import csv
from datetime import datetime
from decimal import Decimal


def detect_petroprix_file(filepath: str) -> bool:
    """Detect if file is a Petroprix fuel export."""
    if not filepath.endswith(".csv"):
        return False
    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            # Check for Petroprix-specific columns
            header_lower = [h.lower() for h in header]
            return "matricula" in header_lower and "litros" in header_lower
    except Exception:
        return False


def parse_petroprix_csv(filepath: str) -> list[dict]:
    """Parse Petroprix fuel CSV export.

    Columns: fecha, matricula, tipo_vehiculo, combustible, nombre, direccion,
             cp, litros, importe_cob, km, tipo_pago
    """
    records = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse date (format: "30-01-2026 14:22:19")
            date_str = row.get("fecha", "").strip()
            if not date_str:
                continue
            try:
                dt = datetime.strptime(date_str, "%d-%m-%Y %H:%M:%S")
            except ValueError:
                continue

            # Parse numeric values (Spanish format: comma decimal)
            liters_str = row.get("litros", "0").replace(",", ".")
            amount_str = row.get("importe_cob", "0").replace(",", ".")

            try:
                liters = Decimal(liters_str)
                amount = Decimal(amount_str)
            except Exception:
                continue

            # Map payment type
            tipo_pago = row.get("tipo_pago", "").strip()
            payment = "tarjeta" if tipo_pago == "1" or "tarjeta" in tipo_pago.lower() else "efectivo"

            records.append({
                "date": dt.date(),
                "liters": liters,
                "amount": amount,
                "provider": "petroprix",
                "payment_method": payment,
                "_plate": row.get("matricula", "").strip(),
                "_address": row.get("direccion", "").strip(),
            })

    return records
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_petroprix_parser.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/parsers/petroprix_parser.py tests/unit/test_petroprix_parser.py tests/fixtures/petroprix_sample.csv
git commit -m "feat(parsers): add Petroprix fuel CSV parser"
```

---

### Task 9: Create Repsol PDF parser

**Files:**
- Create: `scripts/parsers/repsol_parser.py`
- Test: `tests/unit/test_repsol_parser.py`
- Test fixture: Copy `factura (4).pdf` to `tests/fixtures/repsol_sample.pdf`
- Add dependency: `pdfplumber` to requirements.txt

**Step 1: Add pdfplumber dependency**

Add to `requirements.txt`:
```
pdfplumber>=0.10.0
```

Run: `pip install pdfplumber`

**Step 2: Write the failing test**

Create `tests/unit/test_repsol_parser.py`:

```python
"""Tests for Repsol/Solred PDF parser."""
import pytest
from datetime import date
from decimal import Decimal
from scripts.parsers.repsol_parser import parse_repsol_pdf, detect_repsol_file


def test_detect_repsol_file():
    """Should detect Repsol PDF by content."""
    assert detect_repsol_file("tests/fixtures/repsol_sample.pdf") is True
    assert detect_repsol_file("tests/fixtures/prima_sample.csv") is False


def test_parse_repsol_pdf():
    """Should parse Repsol PDF into FuelExpense dicts."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.pdf")

    assert len(records) >= 1

    first = records[0]
    assert "date" in first
    assert "liters" in first
    assert "amount" in first
    assert "_plate" in first
    assert first["provider"] == "repsol"


def test_parse_repsol_extracts_plates():
    """Should extract license plates from PDF."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.pdf")
    plates = set(r["_plate"] for r in records)
    # From sample: 2965MMM and 8921LYW
    assert len(plates) >= 1
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/test_repsol_parser.py -v`
Expected: FAIL

**Step 4: Write minimal implementation**

Create `scripts/parsers/repsol_parser.py`:

```python
"""Parse Repsol/Solred PDF invoices into normalized expense dicts."""
import re
from datetime import datetime
from decimal import Decimal
import pdfplumber


def detect_repsol_file(filepath: str) -> bool:
    """Detect if file is a Repsol/Solred PDF."""
    if not filepath.endswith(".pdf"):
        return False
    try:
        with pdfplumber.open(filepath) as pdf:
            if not pdf.pages:
                return False
            text = pdf.pages[0].extract_text() or ""
            return "SOLRED" in text or "Repsol" in text
    except Exception:
        return False


def parse_repsol_pdf(filepath: str) -> list[dict]:
    """Parse Repsol/Solred PDF invoice.

    Extracts individual refueling operations from page 3 (detail page).
    Format per line: Ref Date/Time Concept Station Kms Quantity ... Amount
    """
    records = []
    current_plate = None
    current_driver = None

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = text.split("\n")

            for line in lines:
                # Detect plate line: "Nº de Tarjeta XXXX Nº de Matrícula PLATE Conductor NAME"
                plate_match = re.search(r"Matrícula\s+(\w+)", line)
                if plate_match:
                    current_plate = plate_match.group(1)
                    driver_match = re.search(r"Conductor\s+(.+?)(?:\s*$)", line)
                    current_driver = driver_match.group(1).strip() if driver_match else None
                    continue

                # Detect fuel line: starts with reference number, contains date
                # Format: "1811940 07/01 15:53 EFITEC 95 N (L) CRED COLLSEROLA ... 47,07 ... 66,79"
                fuel_match = re.match(
                    r"(\d{7})\s+(\d{2}/\d{2})\s+(\d{2}:\d{2})\s+(.+?)\s+(\d+[,\.]\d+)\s+.*?(\d+[,\.]\d+)\s*$",
                    line
                )
                if fuel_match and current_plate:
                    ref, date_str, time_str, concept, liters_str, amount_str = fuel_match.groups()

                    # Parse date (format: "07/01" - need to add year)
                    try:
                        # Assume current year, adjust if needed
                        dt = datetime.strptime(f"{date_str}/2026", "%d/%m/%Y")
                    except ValueError:
                        continue

                    liters = Decimal(liters_str.replace(",", "."))
                    amount = Decimal(amount_str.replace(",", "."))

                    records.append({
                        "date": dt.date(),
                        "liters": liters,
                        "amount": amount,
                        "provider": "repsol",
                        "payment_method": "tarjeta",
                        "_plate": current_plate,
                        "_driver_name": current_driver,
                        "_reference": ref,
                    })

    return records
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_repsol_parser.py -v`
Expected: PASS (may need adjustments based on actual PDF format)

**Step 6: Commit**

```bash
git add scripts/parsers/repsol_parser.py tests/unit/test_repsol_parser.py tests/fixtures/repsol_sample.pdf requirements.txt
git commit -m "feat(parsers): add Repsol/Solred PDF parser"
```

---

## Phase 3: Services

### Task 10: Create incident detection service

**Files:**
- Create: `src/services/incident_detector.py`
- Test: `tests/unit/test_incident_detector.py`

**Step 1: Write the failing test**

Create `tests/unit/test_incident_detector.py`:

```python
"""Tests for incident detection service."""
import pytest
from datetime import datetime
from src.services.incident_detector import is_potential_incident, detect_incidents


def test_is_potential_incident_zero_km_short_time():
    """Trip with 0km and <30s should be flagged."""
    trip = {
        "distance_km": 0,
        "duration_minutes": 0.3,  # 18 seconds
        "gross_amount": 2.85,
    }
    assert is_potential_incident(trip) is True


def test_is_potential_incident_normal_trip():
    """Normal trip should not be flagged."""
    trip = {
        "distance_km": 5.5,
        "duration_minutes": 15,
        "gross_amount": 12.50,
    }
    assert is_potential_incident(trip) is False


def test_is_potential_incident_zero_km_long_time():
    """Trip with 0km but long time (waiting) should not be flagged."""
    trip = {
        "distance_km": 0,
        "duration_minutes": 25,  # 25 minutes waiting
        "gross_amount": 45.00,
    }
    assert is_potential_incident(trip) is False


def test_detect_incidents_returns_list():
    """detect_incidents should return list of trip IDs."""
    trips = [
        {"id": "trip-1", "distance_km": 0, "duration_minutes": 0.2, "gross_amount": 0},
        {"id": "trip-2", "distance_km": 5, "duration_minutes": 10, "gross_amount": 15},
        {"id": "trip-3", "distance_km": 0, "duration_minutes": 0.4, "gross_amount": 2.85},
    ]
    incidents = detect_incidents(trips)
    assert "trip-1" in incidents
    assert "trip-2" not in incidents
    assert "trip-3" in incidents
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_incident_detector.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/services/incident_detector.py`:

```python
"""Detect potential incidents (null tickets) in trip data."""


def is_potential_incident(trip: dict) -> bool:
    """Check if a trip is a potential incident (null ticket).

    Criteria: distance_km == 0 AND duration < 30 seconds (0.5 minutes)
    """
    distance = float(trip.get("distance_km") or 0)
    duration = float(trip.get("duration_minutes") or 0)

    if distance == 0 and duration < 0.5:
        return True

    return False


def detect_incidents(trips: list[dict]) -> list[str]:
    """Return list of trip IDs that are potential incidents."""
    return [t["id"] for t in trips if is_potential_incident(t)]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_incident_detector.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/incident_detector.py tests/unit/test_incident_detector.py
git commit -m "feat(services): add incident detection service"
```

---

### Task 11: Create VISA matching service

**Files:**
- Create: `src/services/visa_matcher.py`
- Test: `tests/unit/test_visa_matcher.py`

**Step 1: Write the failing test**

Create `tests/unit/test_visa_matcher.py`:

```python
"""Tests for VISA payment matching service."""
import pytest
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from src.services.visa_matcher import match_visa_to_trip, calculate_tip


def test_match_visa_to_trip_exact_time():
    """Should match VISA payment to trip within 10 minutes."""
    visa = {
        "date": date(2026, 2, 3),
        "time": time(10, 54, 42),
        "amount": Decimal("28.00"),
    }
    trips = [
        {"id": "trip-1", "ended_at": datetime(2026, 2, 3, 10, 50), "gross_amount": 28.00},
        {"id": "trip-2", "ended_at": datetime(2026, 2, 3, 9, 0), "gross_amount": 28.00},
    ]
    match = match_visa_to_trip(visa, trips)
    assert match["trip_id"] == "trip-1"


def test_match_visa_to_trip_no_match():
    """Should return None when no trip matches."""
    visa = {
        "date": date(2026, 2, 3),
        "time": time(10, 54, 42),
        "amount": Decimal("28.00"),
    }
    trips = [
        {"id": "trip-1", "ended_at": datetime(2026, 2, 3, 8, 0), "gross_amount": 28.00},
    ]
    match = match_visa_to_trip(visa, trips)
    assert match is None


def test_calculate_tip():
    """Should calculate tip as difference between VISA and trip amount."""
    visa_amount = Decimal("30.00")
    trip_amount = Decimal("28.00")
    tip = calculate_tip(visa_amount, trip_amount)
    assert tip == Decimal("2.00")


def test_calculate_tip_no_tip():
    """Should return 0 when amounts match."""
    visa_amount = Decimal("28.00")
    trip_amount = Decimal("28.00")
    tip = calculate_tip(visa_amount, trip_amount)
    assert tip == Decimal("0.00")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_visa_matcher.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/services/visa_matcher.py`:

```python
"""Match VISA payments to trips by time proximity."""
from datetime import datetime, timedelta, date, time
from decimal import Decimal

# Maximum time difference for matching (10 minutes)
MAX_TIME_DIFF_MINUTES = 10


def match_visa_to_trip(visa: dict, trips: list[dict]) -> dict | None:
    """Find the best matching trip for a VISA payment.

    Matches based on time proximity (within 10 minutes of trip end).
    Returns dict with trip_id and tip_amount, or None if no match.
    """
    visa_datetime = datetime.combine(visa["date"], visa["time"])
    max_diff = timedelta(minutes=MAX_TIME_DIFF_MINUTES)

    best_match = None
    best_diff = None

    for trip in trips:
        trip_end = trip.get("ended_at")
        if not trip_end:
            continue

        if isinstance(trip_end, str):
            trip_end = datetime.fromisoformat(trip_end)

        diff = abs(visa_datetime - trip_end)
        if diff <= max_diff:
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_match = trip

    if best_match:
        tip = calculate_tip(visa["amount"], Decimal(str(best_match["gross_amount"])))
        return {
            "trip_id": best_match["id"],
            "tip_amount": tip,
        }

    return None


def calculate_tip(visa_amount: Decimal, trip_amount: Decimal) -> Decimal:
    """Calculate tip as difference between VISA payment and trip amount."""
    diff = visa_amount - trip_amount
    return max(diff, Decimal("0.00"))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_visa_matcher.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/visa_matcher.py tests/unit/test_visa_matcher.py
git commit -m "feat(services): add VISA payment matching service"
```

---

### Task 12: Create settlement calculation service

**Files:**
- Create: `src/services/settlement_calculator.py`
- Test: `tests/unit/test_settlement_calculator.py`

**Step 1: Write the failing test**

Create `tests/unit/test_settlement_calculator.py`:

```python
"""Tests for settlement calculation service."""
import pytest
from decimal import Decimal
from src.services.settlement_calculator import (
    calculate_freenow_net,
    calculate_vat,
    get_driver_percentage,
    calculate_daily_settlement,
)


def test_calculate_freenow_net():
    """FreeNow net = bruto / 1.125 * 1.21"""
    bruto = Decimal("70.20")
    net = calculate_freenow_net(bruto)
    # 70.20 / 1.125 * 1.21 = 75.504
    assert net == Decimal("75.50")  # rounded to 2 decimals


def test_calculate_vat():
    """VAT = total - (total / 1.1)"""
    total = Decimal("197.55")
    vat = calculate_vat(total)
    # 197.55 - (197.55 / 1.1) = 17.959...
    assert vat == Decimal("17.96")


def test_get_driver_percentage_below_threshold():
    """Should return base percentage below threshold."""
    pct = get_driver_percentage(
        total=Decimal("250.00"),
        base_pct=Decimal("40.0"),
        bonus_pct=Decimal("45.0"),
        threshold=Decimal("300.0"),
    )
    assert pct == Decimal("40.0")


def test_get_driver_percentage_above_threshold():
    """Should return bonus percentage at or above threshold."""
    pct = get_driver_percentage(
        total=Decimal("350.00"),
        base_pct=Decimal("40.0"),
        bonus_pct=Decimal("45.0"),
        threshold=Decimal("300.0"),
    )
    assert pct == Decimal("45.0")


def test_calculate_daily_settlement():
    """Full daily settlement calculation."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("127.35"),
        freenow_bruto=Decimal("70.20"),
        uber_net=Decimal("0.00"),
        visa_total=Decimal("102.20"),
        freenow_app_paid=Decimal("51.20"),
        uber_app_paid=Decimal("0.00"),
        freenow_commission=Decimal("10.00"),
        uber_commission=Decimal("0.00"),
        driver_config={
            "commission_base_pct": Decimal("40.0"),
            "commission_bonus_pct": Decimal("45.0"),
            "commission_threshold": Decimal("300.0"),
            "freenow_commission_driver_pct": Decimal("0.0"),
            "uber_commission_driver_pct": Decimal("0.0"),
        },
    )

    assert "rec_total" in result
    assert "vat" in result
    assert "driver_pct" in result
    assert "driver_share" in result
    assert "cash" in result
    assert "debt" in result
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_settlement_calculator.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/services/settlement_calculator.py`:

```python
"""Calculate driver settlements based on trip data and commission rules."""
from decimal import Decimal, ROUND_HALF_UP


def calculate_freenow_net(bruto: Decimal) -> Decimal:
    """Calculate FreeNow net amount: bruto / 1.125 * 1.21"""
    if bruto == 0:
        return Decimal("0.00")
    result = bruto / Decimal("1.125") * Decimal("1.21")
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_vat(total: Decimal) -> Decimal:
    """Calculate VAT (10%): total - (total / 1.1)"""
    if total == 0:
        return Decimal("0.00")
    result = total - (total / Decimal("1.1"))
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_driver_percentage(
    total: Decimal,
    base_pct: Decimal,
    bonus_pct: Decimal,
    threshold: Decimal,
) -> Decimal:
    """Get driver percentage based on total and threshold."""
    if threshold > 0 and total >= threshold:
        return bonus_pct
    return base_pct


def calculate_daily_settlement(
    prima_amount: Decimal,
    freenow_bruto: Decimal,
    uber_net: Decimal,
    visa_total: Decimal,
    freenow_app_paid: Decimal,
    uber_app_paid: Decimal,
    freenow_commission: Decimal,
    uber_commission: Decimal,
    driver_config: dict,
) -> dict:
    """Calculate full daily settlement for a driver.

    Returns dict with all calculated values.
    """
    # Calculate net amounts
    freenow_net = calculate_freenow_net(freenow_bruto)

    # Total revenue
    rec_total = prima_amount + freenow_net + uber_net

    # VAT
    vat = calculate_vat(rec_total)

    # Driver percentage
    driver_pct = get_driver_percentage(
        total=rec_total,
        base_pct=Decimal(str(driver_config["commission_base_pct"])),
        bonus_pct=Decimal(str(driver_config["commission_bonus_pct"])),
        threshold=Decimal(str(driver_config["commission_threshold"])),
    )

    # Commission charges to driver
    freenow_driver_pct = Decimal(str(driver_config["freenow_commission_driver_pct"]))
    uber_driver_pct = Decimal(str(driver_config["uber_commission_driver_pct"]))

    commission_charge = (
        freenow_commission * freenow_driver_pct / 100 +
        uber_commission * uber_driver_pct / 100
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Driver share
    base_imponible = rec_total - vat
    driver_share = (base_imponible * driver_pct / 100 - commission_charge).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Cash calculation
    cash = rec_total - visa_total - freenow_app_paid - uber_app_paid

    # Debt (positive = owner owes driver, negative = driver owes owner)
    debt = driver_share - cash

    return {
        "prima_amount": prima_amount,
        "freenow_bruto": freenow_bruto,
        "freenow_net": freenow_net,
        "uber_net": uber_net,
        "rec_total": rec_total,
        "visa_total": visa_total,
        "freenow_app_paid": freenow_app_paid,
        "uber_app_paid": uber_app_paid,
        "vat": vat,
        "driver_pct": driver_pct,
        "commission_charge": commission_charge,
        "driver_share": driver_share,
        "cash": cash,
        "debt": debt,
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_settlement_calculator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/settlement_calculator.py tests/unit/test_settlement_calculator.py
git commit -m "feat(services): add settlement calculation service"
```

---

## Phase 4: UI - Admin Configuration

### Task 13: Update admin page with commission fields

**Files:**
- Modify: `src/templates/admin_edit_driver.html`
- Modify: `src/routes/admin.py`

**Step 1: Update the template**

Modify `src/templates/admin_edit_driver.html`, add after existing fields:

```html
<hr class="my-4">
<h6>Condiciones de liquidacion</h6>

<div class="row">
    <div class="col-md-4 mb-3">
        <label class="form-label">% base conductor</label>
        <div class="input-group">
            <input type="number" step="0.01" class="form-control" name="commission_base_pct"
                   value="{{ driver.commission_base_pct or 40 }}">
            <span class="input-group-text">%</span>
        </div>
    </div>
    <div class="col-md-4 mb-3">
        <label class="form-label">% bonificado</label>
        <div class="input-group">
            <input type="number" step="0.01" class="form-control" name="commission_bonus_pct"
                   value="{{ driver.commission_bonus_pct or 45 }}">
            <span class="input-group-text">%</span>
        </div>
    </div>
    <div class="col-md-4 mb-3">
        <label class="form-label">Umbral bonificacion</label>
        <div class="input-group">
            <input type="number" step="0.01" class="form-control" name="commission_threshold"
                   value="{{ driver.commission_threshold or 300 }}">
            <span class="input-group-text">EUR</span>
        </div>
        <small class="text-muted">0 = siempre fijo</small>
    </div>
</div>

<div class="row">
    <div class="col-md-6 mb-3">
        <label class="form-label">Comision FreeNow - % conductor</label>
        <div class="input-group">
            <input type="number" step="0.01" class="form-control" name="freenow_commission_driver_pct"
                   value="{{ driver.freenow_commission_driver_pct or 0 }}">
            <span class="input-group-text">%</span>
        </div>
        <small class="text-muted">0% = paga propietario, 50% = a medias, 100% = paga conductor</small>
    </div>
    <div class="col-md-6 mb-3">
        <label class="form-label">Comision Uber - % conductor</label>
        <div class="input-group">
            <input type="number" step="0.01" class="form-control" name="uber_commission_driver_pct"
                   value="{{ driver.uber_commission_driver_pct or 0 }}">
            <span class="input-group-text">%</span>
        </div>
        <small class="text-muted">0% = paga propietario, 50% = a medias, 100% = paga conductor</small>
    </div>
</div>
```

**Step 2: Update the route handler**

Modify `src/routes/admin.py` in the `edit_driver_page` POST handler to save the new fields:

```python
# Add to the existing update logic:
driver.commission_base_pct = float(form.get("commission_base_pct") or 40)
driver.commission_bonus_pct = float(form.get("commission_bonus_pct") or 45)
driver.commission_threshold = float(form.get("commission_threshold") or 300)
driver.freenow_commission_driver_pct = float(form.get("freenow_commission_driver_pct") or 0)
driver.uber_commission_driver_pct = float(form.get("uber_commission_driver_pct") or 0)
```

**Step 3: Test manually**

1. Go to `/admin`
2. Click edit on a driver
3. Verify new fields appear
4. Update values and save
5. Verify values persist

**Step 4: Commit**

```bash
git add src/templates/admin_edit_driver.html src/routes/admin.py
git commit -m "feat(admin): add commission configuration fields to driver edit"
```

---

## Phase 5: UI - Validation Queue

### Task 14: Create validation queue page

**Files:**
- Create: `src/routes/validation.py`
- Create: `src/templates/validation.html`
- Modify: `src/main.py` (register router)
- Modify: `src/templates/base.html` (add nav link)

**Step 1: Create the route**

Create `src/routes/validation.py`:

```python
# src/routes/validation.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.routes.auth import require_admin
from src.database import get_session
from src.models.pending_validation import PendingValidation
from src.models.trip import Trip
from src.template_config import templates, root_path

router = APIRouter()


@router.get("/validacion", response_class=HTMLResponse)
async def validation_page(
    request: Request,
    tab: str = "incidents",
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Show pending validations queue."""
    # Get pending validations by type
    incidents = session.query(PendingValidation).filter_by(
        validation_type="incident", status="pending"
    ).all()

    visa_pending = session.query(PendingValidation).filter_by(
        validation_type="visa_no_match", status="pending"
    ).all()

    fuel_pending = session.query(PendingValidation).filter_by(
        validation_type="fuel_no_match", status="pending"
    ).all()

    # Get related trips for incidents
    incident_trips = {}
    for pv in incidents:
        if pv.trip_id:
            trip = session.get(Trip, pv.trip_id)
            if trip:
                incident_trips[pv.id] = trip

    return templates.TemplateResponse(request, "validation.html", {
        "user": user,
        "tab": tab,
        "incidents": incidents,
        "incident_trips": incident_trips,
        "visa_pending": visa_pending,
        "fuel_pending": fuel_pending,
        "total_pending": len(incidents) + len(visa_pending) + len(fuel_pending),
    })


@router.post("/validacion/{validation_id}/resolve", response_class=HTMLResponse)
async def resolve_validation(
    request: Request,
    validation_id: str,
    action: str = Form(...),
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Resolve a pending validation."""
    from datetime import datetime, timezone

    pv = session.get(PendingValidation, validation_id)
    if not pv:
        return RedirectResponse(url=f"{root_path}/validacion", status_code=303)

    if action == "valid":
        pv.status = "valid"
    elif action == "invalid":
        pv.status = "invalid"

    pv.resolved_at = datetime.now(timezone.utc)
    pv.resolved_by = user.get("name", "admin")
    session.commit()

    return RedirectResponse(url=f"{root_path}/validacion", status_code=303)
```

**Step 2: Create the template**

Create `src/templates/validation.html`:

```html
{% extends "base.html" %}
{% block title %}Validacion - TAXI API{% endblock %}
{% block content %}
<h4>Cola de Validacion</h4>

{% if total_pending > 0 %}
<div class="alert alert-warning">
    <strong>{{ total_pending }}</strong> items pendientes de validar
</div>
{% else %}
<div class="alert alert-success">
    No hay items pendientes
</div>
{% endif %}

<ul class="nav nav-tabs mb-3">
    <li class="nav-item">
        <a class="nav-link {% if tab == 'incidents' %}active{% endif %}"
           href="{{ root_path }}/validacion?tab=incidents">
            Incidencias <span class="badge bg-secondary">{{ incidents|length }}</span>
        </a>
    </li>
    <li class="nav-item">
        <a class="nav-link {% if tab == 'visa' %}active{% endif %}"
           href="{{ root_path }}/validacion?tab=visa">
            VISA sin match <span class="badge bg-secondary">{{ visa_pending|length }}</span>
        </a>
    </li>
    <li class="nav-item">
        <a class="nav-link {% if tab == 'fuel' %}active{% endif %}"
           href="{{ root_path }}/validacion?tab=fuel">
            Combustible <span class="badge bg-secondary">{{ fuel_pending|length }}</span>
        </a>
    </li>
</ul>

{% if tab == 'incidents' %}
<div class="table-responsive">
    <table class="table table-sm">
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Detalles</th>
                <th>Importe</th>
                <th>Acciones</th>
            </tr>
        </thead>
        <tbody>
            {% for pv in incidents %}
            {% set trip = incident_trips.get(pv.id) %}
            <tr>
                <td>{{ trip.started_at.strftime('%d/%m/%Y %H:%M') if trip else '-' }}</td>
                <td>
                    {% if trip %}
                    {{ trip.distance_km or 0 }}km, {{ trip.duration_minutes or 0 }}min
                    {% endif %}
                    <small class="text-muted">{{ pv.details }}</small>
                </td>
                <td>{{ '%.2f'|format(trip.gross_amount) if trip else '-' }} EUR</td>
                <td>
                    <form method="post" action="{{ root_path }}/validacion/{{ pv.id }}/resolve" class="d-inline">
                        <button type="submit" name="action" value="valid" class="btn btn-sm btn-success">Valido</button>
                        <button type="submit" name="action" value="invalid" class="btn btn-sm btn-danger">Incidencia</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="4" class="text-muted">No hay incidencias pendientes</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

{% if tab == 'visa' %}
<div class="table-responsive">
    <table class="table table-sm">
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Importe</th>
                <th>Tarjeta</th>
                <th>Acciones</th>
            </tr>
        </thead>
        <tbody>
            {% for pv in visa_pending %}
            <tr>
                <td>{{ pv.details.get('date', '-') }}</td>
                <td>{{ pv.details.get('amount', '-') }} EUR</td>
                <td>{{ pv.details.get('brand', '') }} ***{{ pv.details.get('card_last4', '') }}</td>
                <td>
                    <form method="post" action="{{ root_path }}/validacion/{{ pv.id }}/resolve" class="d-inline">
                        <button type="submit" name="action" value="valid" class="btn btn-sm btn-success">Asignar</button>
                        <button type="submit" name="action" value="invalid" class="btn btn-sm btn-danger">Descartar</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="4" class="text-muted">No hay pagos VISA pendientes</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

{% if tab == 'fuel' %}
<div class="table-responsive">
    <table class="table table-sm">
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Importe</th>
                <th>Proveedor</th>
                <th>Acciones</th>
            </tr>
        </thead>
        <tbody>
            {% for pv in fuel_pending %}
            <tr>
                <td>{{ pv.details.get('date', '-') }}</td>
                <td>{{ pv.details.get('amount', '-') }} EUR</td>
                <td>{{ pv.details.get('provider', '-') }}</td>
                <td>
                    <form method="post" action="{{ root_path }}/validacion/{{ pv.id }}/resolve" class="d-inline">
                        <button type="submit" name="action" value="valid" class="btn btn-sm btn-success">Asignar</button>
                        <button type="submit" name="action" value="invalid" class="btn btn-sm btn-danger">Descartar</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="4" class="text-muted">No hay combustible pendiente</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

{% endblock %}
```

**Step 3: Register router and add nav link**

Add to `src/main.py`:
```python
from src.routes.validation import router as validation_router
app.include_router(validation_router)
```

Add to `src/templates/base.html` in nav section:
```html
{% if user.role == 'admin' %}
<li class="nav-item"><a class="nav-link" href="{{ root_path }}/validacion">Validacion</a></li>
{% endif %}
```

**Step 4: Commit**

```bash
git add src/routes/validation.py src/templates/validation.html src/main.py src/templates/base.html
git commit -m "feat(ui): add validation queue page"
```

---

## Phase 6: UI - Settlement Page

### Task 15: Create settlement page

**Files:**
- Create: `src/routes/liquidacion.py`
- Create: `src/templates/liquidacion.html`
- Modify: `src/main.py`
- Modify: `src/templates/base.html`

This task is similar to Task 14 but creates the main settlement generation and display page. Due to length, the implementation follows the same pattern with:

1. Route with GET (form + results) and POST (generate settlement)
2. Template with driver selector, date range, and Excel-style table
3. Integration with settlement_calculator service
4. Excel download endpoint

**Step 1-4:** Follow same pattern as Task 14

**Step 5: Commit**

```bash
git add src/routes/liquidacion.py src/templates/liquidacion.html src/main.py src/templates/base.html
git commit -m "feat(ui): add settlement page with Excel-style table"
```

---

### Task 16: Add Excel export

**Files:**
- Create: `src/services/excel_exporter.py`
- Modify: `src/routes/liquidacion.py`

Uses `openpyxl` to generate Excel file matching the original format.

---

## Summary

**Total Tasks:** 16
**Estimated Time:** 2-3 days

**Phases:**
1. Database Models (Tasks 1-6)
2. Parsers (Tasks 7-9)
3. Services (Tasks 10-12)
4. UI - Admin (Task 13)
5. UI - Validation Queue (Task 14)
6. UI - Settlement (Tasks 15-16)

**Dependencies:**
- openpyxl (Excel parsing/export)
- pdfplumber (PDF parsing)

**Testing:**
- Unit tests for all models, parsers, and services
- Manual testing for UI pages
