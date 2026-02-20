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
    # 4 ON entries with known terminal prefixes (TRANSF and C. negative filtered out)
    assert len(records) == 4


def test_lacaixa_terminal_34_maps_to_092():
    """Terminal prefix 34 should map to license 092."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    lic_092 = [r for r in records if r["license_number"] == "092"]
    assert len(lic_092) == 2
    assert lic_092[0]["amount"] == Decimal("152.30")


def test_lacaixa_terminal_35_maps_to_1061():
    """Terminal prefix 35 should map to license 1061."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    lic_1061 = [r for r in records if r["license_number"] == "1061"]
    assert len(lic_1061) == 1
    assert lic_1061[0]["amount"] == Decimal("89.50")


def test_lacaixa_terminal_36_maps_to_361():
    """Terminal prefix 36 should map to license 361."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    lic_361 = [r for r in records if r["license_number"] == "361"]
    # Only ON entry (111.65); C. correction (-0.13) is excluded (negative)
    assert len(lic_361) == 1
    assert lic_361[0]["amount"] == Decimal("111.65")


def test_lacaixa_negative_corrections_excluded():
    """C. correction entries with negative amounts should be excluded."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    # The fixture has C. 363460767 with -0.13 — must not appear
    corrections = [r for r in records if r["amount"] < 1]
    assert len(corrections) == 0


def test_lacaixa_filters_non_tpv_movements():
    """Should filter out non-ON/C. movements like transfers."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    assert all(r["license_number"] in ("092", "1061", "361") for r in records)


def test_lacaixa_dates():
    """Should extract dates from description DDMM, not bank entry date."""
    records = parse_lacaixa_xlsx("tests/fixtures/lacaixa_sample.xlsx")
    dates = {r["date"] for r in records}
    # "ON 340921234 2601" -> day=26, month=01; "ON ...2701" -> day=27, month=01
    assert date(2026, 1, 26) in dates
    assert date(2026, 1, 27) in dates
