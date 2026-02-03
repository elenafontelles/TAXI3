from scripts.parsers.freenow_parser import parse_freenow_csv


def test_parse_freenow_csv():
    trips = parse_freenow_csv("tests/fixtures/freenow_sample.csv")
    assert len(trips) == 3  # CANCELLED row filtered out
    assert trips[0]["source"] == "freenow"
    assert trips[0]["external_id"] == "BK-001"
    assert trips[0]["gross_amount"] == 12.50
    assert trips[0]["commission"] == 0
    assert trips[0]["payout_amount"] == 12.50
    assert trips[0]["tips"] == 0.0
    assert trips[0]["tolls"] == 0.0
    assert trips[0]["taxes_vat"] == 1.25  # 10% of 12.50
    assert trips[0]["payment_method"] == "efectivo"
    assert trips[0]["origin_address"] == "Placa Catalunya"
    assert trips[0]["_driver_name"] == "Juan Garcia"
    assert trips[0]["_plate"] == "1234ABC"


def test_freenow_skips_cancelled():
    trips = parse_freenow_csv("tests/fixtures/freenow_sample.csv")
    external_ids = [t["external_id"] for t in trips]
    assert "BK-003" not in external_ids  # CANCELLED booking excluded


def test_freenow_card_payment():
    trips = parse_freenow_csv("tests/fixtures/freenow_sample.csv")
    assert trips[1]["payment_method"] == "tarjeta"


def test_freenow_tolls():
    trips = parse_freenow_csv("tests/fixtures/freenow_sample.csv")
    assert trips[2]["tolls"] == 1.20  # BK-004
