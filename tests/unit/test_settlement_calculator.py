"""Tests for settlement calculation service."""
from decimal import Decimal
from src.services.settlement_calculator import (
    calculate_freenow_net, calculate_vat, get_driver_percentage, calculate_daily_settlement,
)


def test_calculate_freenow_net():
    bruto = Decimal("70.20")
    net = calculate_freenow_net(bruto)
    # 70.20 - (70.20 / 1.10 * 0.125 * 1.21) = 70.20 - 9.6525 = 60.55
    assert net == Decimal("60.55")


def test_calculate_freenow_net_zero():
    """Zero bruto should return zero."""
    net = calculate_freenow_net(Decimal("0.00"))
    assert net == Decimal("0.00")


def test_calculate_vat():
    total = Decimal("197.55")
    vat = calculate_vat(total)
    assert vat == Decimal("17.96")  # 197.55 - (197.55 / 1.1)


def test_calculate_vat_zero():
    """Zero total should return zero VAT."""
    vat = calculate_vat(Decimal("0.00"))
    assert vat == Decimal("0.00")


def test_get_driver_percentage_below_threshold():
    pct = get_driver_percentage(Decimal("250.00"), Decimal("40.0"), Decimal("45.0"), Decimal("300.0"))
    assert pct == Decimal("40.0")


def test_get_driver_percentage_above_threshold():
    pct = get_driver_percentage(Decimal("350.00"), Decimal("40.0"), Decimal("45.0"), Decimal("300.0"))
    assert pct == Decimal("45.0")


def test_get_driver_percentage_at_threshold():
    """At exactly the threshold, should use bonus percentage."""
    pct = get_driver_percentage(Decimal("300.00"), Decimal("40.0"), Decimal("45.0"), Decimal("300.0"))
    assert pct == Decimal("45.0")


def test_get_driver_percentage_zero_threshold():
    """Zero threshold should always return base percentage."""
    pct = get_driver_percentage(Decimal("500.00"), Decimal("40.0"), Decimal("45.0"), Decimal("0.0"))
    assert pct == Decimal("40.0")


def _default_config(**overrides):
    """Helper to build driver config with defaults."""
    config = {
        "prima_base_pct": Decimal("40.0"),
        "prima_bonus_pct": Decimal("45.0"),
        "commission_threshold": Decimal("300.0"),
        "freenow_commission_driver_pct": Decimal("0.0"),
        "fuel_deducted_from_driver": False,
    }
    config.update(overrides)
    return config


def test_calculate_daily_settlement_basic():
    """Test basic settlement with only prima income."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("200.00"),
        freenow_fixed_bruto=Decimal("0.00"),
        uber_t3_fixed=Decimal("0.00"),
        incidents_amount=Decimal("0.00"),
        tpv_visa_total=Decimal("50.00"),
        freenow_app_paid_bruto=Decimal("0.00"),
        uber_total_payment=Decimal("0.00"),
        fuel_total=Decimal("0.00"),
        other_expenses_total=Decimal("0.00"),
        driver_config=_default_config(),
    )
    # recaudacion_total = 200
    assert result["recaudacion_total"] == Decimal("200.00")
    # recaudacion_neta = 200 (no incidents)
    assert result["recaudacion_neta"] == Decimal("200.00")
    # iva = 200 - (200 / 1.1) = 200 - 181.82 = 18.18
    assert result["iva"] == Decimal("18.18")
    # base_imponible = 200 - 18.18 = 181.82
    assert result["base_imponible"] == Decimal("181.82")
    # driver_pct = 40% (below 300 threshold)
    assert result["driver_pct"] == Decimal("40.0")
    # parte_proporcional = 181.82 * 40 / 100 = 72.73
    assert result["parte_proporcional"] == Decimal("72.73")
    # anticipado = 200 - 50 - 0 - 0 - 0 - 0 = 150
    assert result["anticipado"] == Decimal("150.00")
    # liquidacion = 72.73 - 150 = -77.27 (driver owes)
    assert result["liquidacion"] == Decimal("-77.27")


def test_calculate_daily_settlement_with_incidents():
    """Test settlement with incident deductions."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("300.00"),
        freenow_fixed_bruto=Decimal("0.00"),
        uber_t3_fixed=Decimal("0.00"),
        incidents_amount=Decimal("20.00"),
        tpv_visa_total=Decimal("100.00"),
        freenow_app_paid_bruto=Decimal("0.00"),
        uber_total_payment=Decimal("0.00"),
        fuel_total=Decimal("0.00"),
        other_expenses_total=Decimal("0.00"),
        driver_config=_default_config(),
    )
    # recaudacion_total = 300
    assert result["recaudacion_total"] == Decimal("300.00")
    # recaudacion_neta = 300 - 20 = 280
    assert result["recaudacion_neta"] == Decimal("280.00")
    assert result["incidents_amount"] == Decimal("20.00")
    # driver_pct = 40% (280 below 300)
    assert result["driver_pct"] == Decimal("40.0")


def test_calculate_daily_settlement_with_all_sources():
    """Test settlement with prima + freenow + uber."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("127.35"),
        freenow_fixed_bruto=Decimal("70.20"),
        uber_t3_fixed=Decimal("25.00"),
        incidents_amount=Decimal("0.00"),
        tpv_visa_total=Decimal("80.00"),
        freenow_app_paid_bruto=Decimal("50.00"),
        uber_total_payment=Decimal("60.00"),
        fuel_total=Decimal("0.00"),
        other_expenses_total=Decimal("0.00"),
        driver_config=_default_config(),
    )
    # recaudacion_total = 127.35 + 70.20 + 25 = 222.55
    assert result["recaudacion_total"] == Decimal("222.55")
    # recaudacion_neta = 222.55 (no incidents)
    assert result["recaudacion_neta"] == Decimal("222.55")
    # freenow_app = 50.00 (freenow_commission_driver_pct=0 -> bruto passed through)
    assert result["freenow_app"] == Decimal("50.00")
    # anticipado = 222.55 - 80 - 50 - 60 - 0 - 0 = 32.55
    assert result["anticipado"] == Decimal("32.55")


def test_calculate_daily_settlement_freenow_net_when_commission_shared():
    """When driver pays FreeNow commission, APP amount uses net calculation."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("100.00"),
        freenow_fixed_bruto=Decimal("50.00"),
        uber_t3_fixed=Decimal("0.00"),
        incidents_amount=Decimal("0.00"),
        tpv_visa_total=Decimal("50.00"),
        freenow_app_paid_bruto=Decimal("50.00"),
        uber_total_payment=Decimal("0.00"),
        fuel_total=Decimal("0.00"),
        other_expenses_total=Decimal("0.00"),
        driver_config=_default_config(freenow_commission_driver_pct=Decimal("100.0")),
    )
    # freenow_app should use calculate_freenow_net: 50 - (50/1.10*0.125*1.21) = 50 - 6.875 = 43.13
    assert result["freenow_app"] == Decimal("43.13")


def test_calculate_daily_settlement_with_fuel_deducted():
    """Test settlement when fuel is deducted from driver."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("200.00"),
        freenow_fixed_bruto=Decimal("0.00"),
        uber_t3_fixed=Decimal("0.00"),
        incidents_amount=Decimal("0.00"),
        tpv_visa_total=Decimal("50.00"),
        freenow_app_paid_bruto=Decimal("0.00"),
        uber_total_payment=Decimal("0.00"),
        fuel_total=Decimal("30.00"),
        other_expenses_total=Decimal("0.00"),
        driver_config=_default_config(fuel_deducted_from_driver=True),
    )
    # anticipado = 200 - 50 - 0 - 0 - 0 - 30 = 120
    assert result["anticipado"] == Decimal("120.00")
    assert result["fuel_total"] == Decimal("30.00")


def test_calculate_daily_settlement_fuel_not_deducted():
    """When fuel not deducted from driver, fuel doesn't reduce anticipado."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("200.00"),
        freenow_fixed_bruto=Decimal("0.00"),
        uber_t3_fixed=Decimal("0.00"),
        incidents_amount=Decimal("0.00"),
        tpv_visa_total=Decimal("50.00"),
        freenow_app_paid_bruto=Decimal("0.00"),
        uber_total_payment=Decimal("0.00"),
        fuel_total=Decimal("30.00"),
        other_expenses_total=Decimal("0.00"),
        driver_config=_default_config(fuel_deducted_from_driver=False),
    )
    # anticipado = 200 - 50 - 0 - 0 - 0 - 0 = 150 (fuel NOT deducted)
    assert result["anticipado"] == Decimal("150.00")


def test_calculate_daily_settlement_with_other_expenses():
    """Test settlement with other expenses deducted."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("200.00"),
        freenow_fixed_bruto=Decimal("0.00"),
        uber_t3_fixed=Decimal("0.00"),
        incidents_amount=Decimal("0.00"),
        tpv_visa_total=Decimal("50.00"),
        freenow_app_paid_bruto=Decimal("0.00"),
        uber_total_payment=Decimal("0.00"),
        fuel_total=Decimal("0.00"),
        other_expenses_total=Decimal("15.00"),
        driver_config=_default_config(),
    )
    # anticipado = 200 - 50 - 0 - 0 - 15 - 0 = 135
    assert result["anticipado"] == Decimal("135.00")
    assert result["other_expenses_total"] == Decimal("15.00")


def test_calculate_daily_settlement_bonus_threshold():
    """Test that bonus percentage kicks in above threshold."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("350.00"),
        freenow_fixed_bruto=Decimal("0.00"),
        uber_t3_fixed=Decimal("0.00"),
        incidents_amount=Decimal("0.00"),
        tpv_visa_total=Decimal("100.00"),
        freenow_app_paid_bruto=Decimal("0.00"),
        uber_total_payment=Decimal("0.00"),
        fuel_total=Decimal("0.00"),
        other_expenses_total=Decimal("0.00"),
        driver_config=_default_config(),
    )
    # recaudacion_neta = 350, above threshold 300
    assert result["driver_pct"] == Decimal("45.0")


def test_calculate_daily_settlement_returns_all_keys():
    """Verify all expected keys are present."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("100.00"),
        freenow_fixed_bruto=Decimal("0.00"),
        uber_t3_fixed=Decimal("0.00"),
        incidents_amount=Decimal("0.00"),
        tpv_visa_total=Decimal("0.00"),
        freenow_app_paid_bruto=Decimal("0.00"),
        uber_total_payment=Decimal("0.00"),
        fuel_total=Decimal("0.00"),
        other_expenses_total=Decimal("0.00"),
        driver_config=_default_config(),
    )
    expected_keys = {
        "prima_amount", "freenow_fixed_bruto", "uber_t3_fixed",
        "recaudacion_total", "incidents_amount", "recaudacion_neta",
        "iva", "base_imponible", "driver_pct", "parte_proporcional",
        "tpv_visa_total", "freenow_app", "uber_total_payment",
        "fuel_total", "other_expenses_total", "anticipado", "liquidacion",
    }
    assert set(result.keys()) == expected_keys
