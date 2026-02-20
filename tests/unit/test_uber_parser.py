"""Tests for Uber payments CSV parser."""
from datetime import date
from decimal import Decimal
from scripts.parsers.uber_parser import parse_uber_csv, detect_uber_file


def test_detect_uber_file():
    """Should detect Uber CSV by headers."""
    assert detect_uber_file("tests/fixtures/uber_sample.csv") is True


def test_detect_uber_file_rejects_non_uber():
    """Should reject non-Uber files."""
    assert detect_uber_file("tests/fixtures/lacaixa_sample.xlsx") is False


def test_parse_uber_csv_aggregates_by_day():
    """Should aggregate trip rows into daily summaries per driver."""
    records = parse_uber_csv("tests/fixtures/uber_sample.csv")
    # 2 days: 2026-01-29 (2 trips) and 2026-01-30 (3 trips incl. fare adjust)
    # so.payout row is excluded
    assert len(records) == 2


def test_uber_day1_totals():
    """Day 2026-01-29: 2 trips, no taximeter."""
    records = parse_uber_csv("tests/fixtures/uber_sample.csv")
    day1 = [r for r in records if r["date"] == date(2026, 1, 29)][0]
    # t3_fixed = (29.08 - 0) + (21.47 - 0) = 50.55
    assert day1["t3_fixed"] == Decimal("50.55")
    # total_payment = 29.08 + 21.47 = 50.55
    assert day1["total_payment"] == Decimal("50.55")
    assert day1["_driver_name"] == "IVAN ALSINA BURGOS"


def test_uber_day2_with_taximeter():
    """Day 2026-01-30: trip with taximeter=38.00 + normal trip + fare adjust."""
    records = parse_uber_csv("tests/fixtures/uber_sample.csv")
    day2 = [r for r in records if r["date"] == date(2026, 1, 30)][0]
    # t3_fixed = (33.44 - 38.00) + (10.56 - 0) + (3.00 - 0) = -4.56 + 10.56 + 3.00 = 9.00
    assert day2["t3_fixed"] == Decimal("9.00")
    # total_payment = 37.74 + 10.56 + 3.00 = 51.30
    assert day2["total_payment"] == Decimal("51.30")
    # taximeter = 38.00
    assert day2["taximeter"] == Decimal("38.00")


def test_uber_excludes_payout_rows():
    """so.payout rows should be excluded from results."""
    records = parse_uber_csv("tests/fixtures/uber_sample.csv")
    # Only trip dates should appear, not the payout date (2026-02-02)
    dates = {r["date"] for r in records}
    assert date(2026, 2, 2) not in dates


def test_uber_includes_fare_adjustments():
    """trip fare adjust order rows should be included."""
    records = parse_uber_csv("tests/fixtures/uber_sample.csv")
    day2 = [r for r in records if r["date"] == date(2026, 1, 30)][0]
    # total_earnings includes fare adjust: 33.44 + 10.56 + 3.00 = 47.00
    assert day2["total_earnings"] == Decimal("47.00")
