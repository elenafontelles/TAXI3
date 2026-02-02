from scripts.parsers.freenow_parser import parse_freenow_csv


def test_parse_freenow_csv():
    trips = parse_freenow_csv("tests/fixtures/freenow_sample.csv")
    assert len(trips) == 3
    assert trips[0]["source"] == "freenow"
    assert trips[0]["external_id"] == "FN001"
    assert trips[0]["gross_amount"] == 12.50
    assert trips[0]["commission"] == 1.88
    assert trips[0]["payout_amount"] == 10.62
    assert trips[0]["distance_km"] == 3.2
