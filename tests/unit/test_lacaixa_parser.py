"""Tests for La Caixa VISA parser."""
import pytest
from datetime import date, time
from decimal import Decimal
from scripts.parsers.lacaixa_parser import parse_lacaixa_xlsx, detect_lacaixa_file


def test_detect_lacaixa_file():
    """Should detect La Caixa file by content."""
    assert detect_lacaixa_file("tests/fixtures/lacaixa_sample.xlsx") is True


def test_parse_lacaixa_xlsx():
    """Should parse La Caixa XLSX into payment dicts."""
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
