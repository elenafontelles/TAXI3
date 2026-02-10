"""Tests for Uber daily summary XLSX parser."""
from datetime import date
from decimal import Decimal
from scripts.parsers.uber_parser import parse_uber_xlsx, detect_uber_file


def test_detect_uber_file():
    """Should detect Uber XLSX by headers."""
    assert detect_uber_file("tests/fixtures/uber_sample.xlsx") is True


def test_detect_uber_file_rejects_non_uber():
    """Should reject non-Uber XLSX files."""
    assert detect_uber_file("tests/fixtures/lacaixa_sample.xlsx") is False


def test_parse_uber_xlsx():
    """Should parse Uber XLSX into daily summary dicts."""
    records = parse_uber_xlsx("tests/fixtures/uber_sample.xlsx")
    assert len(records) == 3


def test_uber_parser_first_record():
    """Should correctly parse first record values."""
    records = parse_uber_xlsx("tests/fixtures/uber_sample.xlsx")
    first = records[0]
    assert first["license_number"] == "1061"
    assert first["date"] == date(2026, 1, 27)
    assert first["total_earnings"] == Decimal("85.50")
    assert first["taximeter"] == Decimal("60.00")
    assert first["refund"] == Decimal("0.00")
    assert first["adjustments"] == Decimal("2.50")
    assert first["t3_fixed"] == Decimal("25.00")
    assert first["total_payment"] == Decimal("60.50")


def test_uber_parser_multiple_licenses():
    """Should handle multiple license numbers."""
    records = parse_uber_xlsx("tests/fixtures/uber_sample.xlsx")
    licenses = {r["license_number"] for r in records}
    assert "1061" in licenses
    assert "092" in licenses
