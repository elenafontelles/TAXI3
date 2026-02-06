"""Tests for settlement calculation service."""
import pytest
from decimal import Decimal
from src.services.settlement_calculator import (
    calculate_freenow_net, calculate_vat, get_driver_percentage, calculate_daily_settlement,
)


def test_calculate_freenow_net():
    bruto = Decimal("70.20")
    net = calculate_freenow_net(bruto)
    assert net == Decimal("75.50")  # 70.20 / 1.125 * 1.21 rounded


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


def test_calculate_daily_settlement():
    result = calculate_daily_settlement(
        prima_amount=Decimal("127.35"),
        freenow_bruto=Decimal("70.20"),
        uber_net=Decimal("0.00"),
        visa_total=Decimal("102.20"),
        freenow_app_paid=Decimal("51.20"),
        uber_app_paid=Decimal("0.00"),
        freenow_commission=Decimal("10.00"),
        uber_commission=Decimal("0.00"),
        driver_config={
            "commission_base_pct": Decimal("40.0"),
            "commission_bonus_pct": Decimal("45.0"),
            "commission_threshold": Decimal("300.0"),
            "freenow_commission_driver_pct": Decimal("0.0"),
            "uber_commission_driver_pct": Decimal("0.0"),
        },
    )
    assert "rec_total" in result
    assert "vat" in result
    assert "driver_pct" in result
    assert "driver_share" in result
    assert "cash" in result
    assert "debt" in result


def test_calculate_daily_settlement_values():
    """Verify calculated values in settlement."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("127.35"),
        freenow_bruto=Decimal("70.20"),
        uber_net=Decimal("0.00"),
        visa_total=Decimal("102.20"),
        freenow_app_paid=Decimal("51.20"),
        uber_app_paid=Decimal("0.00"),
        freenow_commission=Decimal("10.00"),
        uber_commission=Decimal("0.00"),
        driver_config={
            "commission_base_pct": Decimal("40.0"),
            "commission_bonus_pct": Decimal("45.0"),
            "commission_threshold": Decimal("300.0"),
            "freenow_commission_driver_pct": Decimal("0.0"),
            "uber_commission_driver_pct": Decimal("0.0"),
        },
    )
    # freenow_net = 70.20 / 1.125 * 1.21 = 75.50
    assert result["freenow_net"] == Decimal("75.50")
    # rec_total = 127.35 + 75.50 + 0.00 = 202.85
    assert result["rec_total"] == Decimal("202.85")
    # vat = 202.85 - (202.85 / 1.1) = 18.44
    assert result["vat"] == Decimal("18.44")
    # driver_pct = 40.0 (below threshold of 300)
    assert result["driver_pct"] == Decimal("40.0")
    # commission_charge = 0 (driver pays 0% of commissions)
    assert result["commission_charge"] == Decimal("0.00")
    # base_imponible = 202.85 - 18.44 = 184.41
    # driver_share = 184.41 * 40 / 100 - 0 = 73.76
    assert result["driver_share"] == Decimal("73.76")
    # cash = 202.85 - 102.20 - 51.20 - 0 = 49.45
    assert result["cash"] == Decimal("49.45")
    # debt = 73.76 - 49.45 = 24.31 (owner owes driver)
    assert result["debt"] == Decimal("24.31")


def test_calculate_daily_settlement_with_commission_charge():
    """Test settlement when driver pays part of app commissions."""
    result = calculate_daily_settlement(
        prima_amount=Decimal("100.00"),
        freenow_bruto=Decimal("0.00"),
        uber_net=Decimal("50.00"),
        visa_total=Decimal("50.00"),
        freenow_app_paid=Decimal("0.00"),
        uber_app_paid=Decimal("50.00"),
        freenow_commission=Decimal("0.00"),
        uber_commission=Decimal("12.50"),  # 25% Uber commission
        driver_config={
            "commission_base_pct": Decimal("50.0"),
            "commission_bonus_pct": Decimal("55.0"),
            "commission_threshold": Decimal("200.0"),
            "freenow_commission_driver_pct": Decimal("0.0"),
            "uber_commission_driver_pct": Decimal("50.0"),  # Driver pays 50% of Uber commission
        },
    )
    # commission_charge = 12.50 * 50 / 100 = 6.25
    assert result["commission_charge"] == Decimal("6.25")
