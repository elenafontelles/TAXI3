"""Tests for Repsol/Solred fuel XLSX parser."""
import pytest
from datetime import date
from decimal import Decimal
from scripts.parsers.repsol_parser import parse_repsol_pdf, detect_repsol_file


def test_detect_repsol_file():
    """Should detect Solred XLSX by headers (Fecha + Importe)."""
    assert detect_repsol_file("tests/fixtures/repsol_sample.xlsx") is True


def test_detect_repsol_file_rejects_non_xlsx():
    """Should reject non-XLSX files and XLSX without expected headers."""
    assert detect_repsol_file("tests/fixtures/repsol_sample.pdf") is False
    assert detect_repsol_file("tests/fixtures/petroprix_sample.csv") is False
    assert detect_repsol_file("tests/fixtures/uber_sample.xlsx") is False


def test_parse_repsol_record_count():
    """Should parse valid transactions and skip '---' plates and zero amounts."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.xlsx")
    assert len(records) == 5


def test_parse_repsol_extracts_plates():
    """Should extract license plates from Matrícula column."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.xlsx")
    plates = {r["_plate"] for r in records}
    assert "2965MMM" in plates
    assert "8921LYW" in plates


def test_parse_repsol_first_record_values():
    """Should parse transaction values correctly."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.xlsx")
    mmm_records = [r for r in records if r["_plate"] == "2965MMM"]
    assert len(mmm_records) == 2

    first = mmm_records[0]
    assert first["date"] == date(2026, 1, 7)
    assert first["liters"] == Decimal("47.070")
    assert first["amount"] == Decimal("66.79")


def test_parse_repsol_provider_is_solred():
    """All records should have provider='solred'."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.xlsx")
    for r in records:
        assert r["provider"] == "solred"


def test_parse_repsol_all_records_have_tarjeta():
    """Solred invoices are always fuel card payments."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.xlsx")
    for r in records:
        assert r["payment_method"] == "tarjeta"


def test_parse_repsol_amounts_are_decimal():
    """All amounts and liters should be Decimal."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.xlsx")
    for r in records:
        assert isinstance(r["liters"], Decimal)
        assert isinstance(r["amount"], Decimal)
        assert r["amount"] > 0


def test_parse_repsol_year_extraction():
    """All dates should be in January 2026."""
    records = parse_repsol_pdf("tests/fixtures/repsol_sample.xlsx")
    for r in records:
        assert r["date"].year == 2026
        assert r["date"].month == 1
