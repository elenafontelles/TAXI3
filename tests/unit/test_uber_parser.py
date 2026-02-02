from scripts.parsers.uber_parser import parse_uber_csv


def test_parse_uber_csv():
    trips = parse_uber_csv("tests/fixtures/uber_sample.csv")
    assert len(trips) == 3
    assert trips[0]["source"] == "uber"
    assert "gross_amount" in trips[0]
    assert "started_at" in trips[0]
    assert trips[0]["external_id"] == "UBER001"


def test_uber_parser_amounts():
    trips = parse_uber_csv("tests/fixtures/uber_sample.csv")
    assert trips[0]["gross_amount"] == 25.50
    assert trips[0]["tips"] == 3.00
    assert trips[0]["tolls"] == 0.00
