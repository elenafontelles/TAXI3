"""Tests for Petroprix fuel CSV parser."""
import pytest
from datetime import date
from decimal import Decimal
from scripts.parsers.petroprix_parser import parse_petroprix_csv, detect_petroprix_file


def test_detect_petroprix_file():
    """Should detect Petroprix CSV by columns."""
    assert detect_petroprix_file("tests/fixtures/petroprix_sample.csv") is True


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


def test_parse_petroprix_first_record_values():
    """Should parse European decimal format correctly."""
    records = parse_petroprix_csv("tests/fixtures/petroprix_sample.csv")
    first = records[0]
    # First row: 30-01-2026 14:22:19, 0397MSS, litros=30,82, importe=40,00, Tarjeta
    assert first["date"] == date(2026, 1, 30)
    assert first["liters"] == Decimal("30.82")
    assert first["amount"] == Decimal("40.00")
    assert first["_plate"] == "0397MSS"
    assert first["payment_method"] == "tarjeta"


def test_parse_petroprix_efectivo_payment():
    """Should detect efectivo payment correctly."""
    records = parse_petroprix_csv("tests/fixtures/petroprix_sample.csv")
    # Second row has Efectivo payment
    second = records[1]
    assert second["payment_method"] == "efectivo"


def test_parse_petroprix_record_count():
    """Should parse all records from sample file."""
    records = parse_petroprix_csv("tests/fixtures/petroprix_sample.csv")
    # Sample file has 13 data rows
    assert len(records) == 13


def test_detect_non_petroprix_file():
    """Should return False for non-Petroprix CSV files."""
    assert detect_petroprix_file("tests/fixtures/freenow_sample.csv") is False
    assert detect_petroprix_file("tests/fixtures/nonexistent.csv") is False
    assert detect_petroprix_file("tests/fixtures/some_file.txt") is False
