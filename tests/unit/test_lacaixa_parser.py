"""Tests for La Caixa bank statement parser."""
from datetime import date
from decimal import Decimal
from scripts.parsers.lacaixa_parser import parse_lacaixa_xlsx, detect_lacaixa_file


def test_detect_lacaixa_file():
    """Should detect La Caixa bank statement by content."""
    assert detect_lacaixa_file("tests/fixtures/lacaixa_sample.xlsx") is True


def test_detect_lacaixa_rejects_non_lacaixa():
    """Should reject non-La Caixa XLSX files."""
    assert detect_lacaixa_file("tests/fixtures/uber_sample.xlsx") is False


def test_parse_lacaixa_xlsx():
    """Should parse La Caixa bank statement into TPV daily totals."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    # 4 ON-prefix rows out of 5 total (TRANSFERENCIA is filtered out)
    assert len(records) == 4


def test_lacaixa_on34_maps_to_092():
    """ON34 should map to license 092."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    on34_records = [r for r in records if r["license_number"] == "092"]
    assert len(on34_records) == 2  # Two ON34 entries
    assert on34_records[0]["amount"] == Decimal("152.30")


def test_lacaixa_on35_maps_to_1061():
    """ON35 should map to license 1061."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    on35_records = [r for r in records if r["license_number"] == "1061"]
    assert len(on35_records) == 1
    assert on35_records[0]["amount"] == Decimal("89.50")


def test_lacaixa_filters_non_on_movements():
    """Should filter out non-ON34/ON35/ON36 movements."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    # TRANSFERENCIA row should not appear
    assert all(r["license_number"] in ("092", "1061", "361") for r in records)


def test_lacaixa_dates():
    """Should correctly parse dates."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    dates = {r["date"] for r in records}
    assert date(2026, 1, 27) in dates
    assert date(2026, 1, 28) in dates
