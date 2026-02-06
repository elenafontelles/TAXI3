"""Tests for Repsol/Solred fuel PDF parser."""
import pytest
from datetime import date
from decimal import Decimal
from scripts.parsers.repsol_parser import parse_repsol_pdf, detect_repsol_file


def test_detect_repsol_file():
    """Should detect Repsol/Solred PDF by content."""
    assert detect_repsol_file("tests/fixtures/repsol_sample.pdf") is True


def test_detect_repsol_file_rejects_non_pdf():
    """Should reject non-PDF files."""
    assert detect_repsol_file("tests/fixtures/petroprix_sample.csv") is False
    assert detect_repsol_file("tests/fixtures/nonexistent.pdf") is False
    assert detect_repsol_file("tests/fixtures/some_file.txt") is False


def test_parse_repsol_pdf():
    """Should parse Repsol PDF into FuelExpense dicts."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.pdf")

    assert len(records) >= 1

    first = records[0]
    assert "date" in first
    assert "liters" in first
    assert "amount" in first
    assert "_plate" in first
    assert "payment_method" in first
    assert first["provider"] == "repsol"


def test_parse_repsol_all_records_have_tarjeta():
    """Repsol/Solred invoices are always fuel card payments."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.pdf")
    for r in records:
        assert r["payment_method"] == "tarjeta"


def test_parse_repsol_extracts_plates():
    """Should extract license plates from the PDF."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.pdf")

    plates = {r["_plate"] for r in records}
    # Sample PDF contains plates 2965MMM and 8921LYW
    assert "2965MMM" in plates
    assert "8921LYW" in plates


def test_parse_repsol_extracts_driver():
    """Should extract driver name when available."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.pdf")

    # Find a record with driver info (2965MMM has IVAN ALSINA)
    records_with_driver = [r for r in records if r.get("_driver")]
    assert len(records_with_driver) >= 1

    driver_names = {r["_driver"] for r in records_with_driver}
    assert "IVAN ALSINA" in driver_names


def test_parse_repsol_record_count():
    """Should parse all transactions from sample file."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.pdf")
    # Sample file has 2 transactions for 2965MMM and 11 for 8921LYW
    assert len(records) == 13


def test_parse_repsol_first_record_values():
    """Should parse transaction values correctly."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.pdf")

    # Find first transaction for plate 2965MMM (07/01 at 15:53)
    mmm_records = [r for r in records if r["_plate"] == "2965MMM"]
    assert len(mmm_records) >= 1

    first = mmm_records[0]
    # 07/01/2026, 47.07L, 66.79 EUR (Importe Total after discount)
    assert first["date"] == date(2026, 1, 7)
    assert first["liters"] == Decimal("47.07")
    assert first["amount"] == Decimal("66.79")


def test_parse_repsol_spanish_decimal_format():
    """Should handle Spanish decimal format (comma as separator)."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.pdf")

    # All amounts should be Decimal, not float
    for r in records:
        assert isinstance(r["liters"], Decimal)
        assert isinstance(r["amount"], Decimal)
        # Liters should be reasonable values (1-100L typically)
        assert Decimal("1") <= r["liters"] <= Decimal("100")
        # Amounts should be reasonable (10-200 EUR typically)
        assert Decimal("10") <= r["amount"] <= Decimal("200")


def test_parse_repsol_year_extraction():
    """Should extract year from invoice date range."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.pdf")

    # All dates should be in 2026 (from "01/01/2026 AL 31/01/2026")
    for r in records:
        assert r["date"].year == 2026
