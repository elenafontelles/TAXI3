from scripts.parsers.prima_parser import parse_prima_csv


def test_parse_prima_csv():
    trips = parse_prima_csv("tests/fixtures/prima_sample.csv")
    assert len(trips) == 3
    assert trips[0]["source"] == "prima"
    assert trips[0]["external_id"] == "T001"
    assert trips[0]["gross_amount"] == 12.50
    assert trips[0]["commission"] == 0
    assert trips[0]["payout_amount"] == 12.50
    assert trips[0]["distance_km"] == 3.20
    assert trips[0]["payment_method"] == "efectivo"
    assert trips[0]["tariff_code"] == "T1"
    assert trips[0]["_driver_code"] == "D001"
    assert trips[0]["_license"] == "BCN-1234"


def test_prima_coordinates():
    trips = parse_prima_csv("tests/fixtures/prima_sample.csv")
    assert trips[0]["origin_lat"] == 41.2131
    assert trips[0]["origin_lng"] == 2.0564
    assert trips[1]["dest_lat"] == 41.385


def test_prima_addresses():
    trips = parse_prima_csv("tests/fixtures/prima_sample.csv")
    assert trips[0]["origin_address"] == "Gran Via 100 Barcelona"
    assert trips[0]["dest_address"] == "Diagonal 200 Barcelona"


def test_prima_missing_coords():
    trips = parse_prima_csv("tests/fixtures/prima_sample.csv")
    assert trips[2]["origin_lat"] is None
    assert trips[2]["origin_lng"] is None


def test_prima_time_column():
    """Time column (HH:MM:SS) should be used for duration_minutes."""
    trips = parse_prima_csv("tests/fixtures/prima_sample.csv")
    assert trips[0]["duration_minutes"] == 12.0   # 0:12:00
    assert trips[1]["duration_minutes"] == 18.0   # 0:18:00
    assert trips[2]["duration_minutes"] == 8.0    # 0:08:00


def test_prima_km_free():
    """km_free column should be parsed from Prima CSV."""
    trips = parse_prima_csv("tests/fixtures/prima_sample.csv")
    assert trips[0]["km_free"] == 1.80
    assert trips[1]["km_free"] == 2.30
    assert trips[2]["km_free"] == 0.90
