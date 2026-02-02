from scripts.parsers.prima_parser import parse_prima_csv


def test_parse_prima_csv():
    shifts = parse_prima_csv("tests/fixtures/prima_sample.csv")
    assert len(shifts) == 3
    assert shifts[0]["source"] == "prima"
    assert shifts[0]["external_id"] == "PRIMA001"
    assert shifts[0]["km_free"] == 45.0
    assert shifts[0]["km_occupied"] == 120.5
    assert shifts[0]["total_earnings"] == 350.00
