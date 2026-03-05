"""Calculate driver settlements based on trip data and commission rules."""
from decimal import Decimal, ROUND_HALF_UP


def calculate_freenow_net(bruto: Decimal) -> Decimal:
    """Calculate net amount FreeNow pays to owner after commission.

    Commission = 12.5% of bruto, then 21% IVA on the commission.
    net = bruto - (bruto * 12.5% * 1.21)

    Example with bruto=100:
      commission = 100 * 0.125 = 12.50
      commission + IVA = 12.50 * 1.21 = 15.13
      net = 100 - 15.13 = 84.88

    Args:
        bruto: FreeNow gross amount (what the passenger paid)

    Returns:
        Net amount paid to owner, rounded to 2 decimal places
    """
    if bruto == 0:
        return Decimal("0.00")
    commission = bruto * Decimal("0.125")
    commission_with_vat = commission * Decimal("1.21")
    result = bruto - commission_with_vat
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_vat(total: Decimal) -> Decimal:
    """Calculate VAT (10%) from total amount.

    Formula: total - (total / 1.1)

    Args:
        total: Total amount including VAT

    Returns:
        VAT amount rounded to 2 decimal places
    """
    if total == 0:
        return Decimal("0.00")
    result = total - (total / Decimal("1.1"))
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_driver_percentage(
    total: Decimal,
    base_pct: Decimal,
    bonus_pct: Decimal,
    threshold: Decimal,
) -> Decimal:
    """Get driver commission percentage based on total earnings.

    If total >= threshold, driver gets bonus percentage.
    If threshold is 0, always return base percentage.

    Args:
        total: Total earnings for the period
        base_pct: Base commission percentage
        bonus_pct: Bonus commission percentage when threshold is met
        threshold: Minimum total to qualify for bonus percentage

    Returns:
        Applicable driver percentage
    """
    if threshold > 0 and total >= threshold:
        return bonus_pct
    return base_pct


def calculate_daily_settlement(
    prima_amount: Decimal,
    freenow_fixed_bruto: Decimal,
    freenow_fixed_tips: Decimal,
    uber_t3_fixed: Decimal,
    incidents_amount: Decimal,
    tpv_visa_total: Decimal,
    freenow_app_paid_bruto: Decimal,
    freenow_app_tips: Decimal,
    uber_total_payment: Decimal,
    fuel_total: Decimal,
    other_expenses_total: Decimal,
    driver_config: dict,
    freenow_adjustments: Decimal = Decimal("0.00"),
) -> dict:
    """Calculate complete daily settlement for a driver.

    Args:
        prima_amount: Prima taxi meter earnings
        freenow_fixed_bruto: FreeNow FIXED fare gross amount (adds to recaudacion)
        freenow_fixed_tips: FreeNow FIXED tips (added after commission)
        uber_t3_fixed: Uber T3 fixed amount (adds to recaudacion)
        incidents_amount: Total incident amounts to deduct
        tpv_visa_total: Total TPV/VISA daily total
        freenow_app_paid_bruto: FreeNow APP-paid FIXED fare gross (paid by app)
        freenow_app_tips: FreeNow APP-paid FIXED tips (added after commission)
        uber_total_payment: Uber total payment (paid by app)
        fuel_total: Total fuel expenses
        other_expenses_total: Total other expenses
        driver_config: Dict with driver commission settings:
        freenow_adjustments: FreeNow otros/incentivos adjustments (net, added to freenow_fixed)
            - prima_base_pct: Base driver percentage
            - prima_bonus_pct: Bonus percentage above threshold
            - commission_threshold: Threshold for bonus percentage
            - freenow_commission_driver_pct: % of FreeNow commission driver pays
            - fuel_deducted_from_driver: Whether fuel is deducted from driver

    Returns:
        Dict with all settlement values
    """
    # 1. FreeNow fixed: net or bruto depending on who pays the commission
    #    Tips are added AFTER commission deduction (no commission on tips)
    _fn_pct_raw = driver_config.get("freenow_commission_driver_pct") or 0
    freenow_commission_driver_pct = Decimal(str(_fn_pct_raw))
    if freenow_commission_driver_pct > 0:
        freenow_fixed = calculate_freenow_net(freenow_fixed_bruto) + freenow_fixed_tips
    else:
        freenow_fixed = freenow_fixed_bruto + freenow_fixed_tips

    # Add FreeNow adjustments (otros/incentivos) — net amounts, no commission
    freenow_fixed = freenow_fixed + freenow_adjustments

    # Recaudacion total = prima + freenow_fixed (net or bruto) + uber_t3_fixed
    recaudacion_total = prima_amount + freenow_fixed + uber_t3_fixed

    # 2. Recaudacion neta = recaudacion_total - incidencias
    recaudacion_neta = recaudacion_total - incidents_amount

    # 3. IVA = 10% de recaudacion_neta
    iva = calculate_vat(recaudacion_neta)

    # 4. Base imponible = recaudacion_neta - IVA
    base_imponible = recaudacion_neta - iva

    # 5. Porcentaje taxista
    driver_pct = get_driver_percentage(
        recaudacion_neta,
        Decimal(str(driver_config["prima_base_pct"])),
        Decimal(str(driver_config["prima_bonus_pct"])),
        Decimal(str(driver_config["commission_threshold"])),
    )

    # 6. Parte proporcional = base_imponible * pct / 100
    parte_proporcional = (
        base_imponible * driver_pct / 100
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # 7. FreeNow APP: si comision driver = 0, propietario asume comision
    #    Tips added AFTER commission (no commission on tips)
    #    Adjustments (otros/incentivos) are paid via transfer, count as app payment
    if freenow_commission_driver_pct == 0:
        freenow_app = freenow_app_paid_bruto + freenow_app_tips + freenow_adjustments
    else:
        freenow_app = calculate_freenow_net(freenow_app_paid_bruto) + freenow_app_tips + freenow_adjustments

    # 8. Anticipado = recaudacion_neta - tpv_visa - freenow_app - uber_total_payment
    #               - otros_gastos - gasolina (si fuel_deducted_from_driver)
    fuel_deducted = bool(driver_config.get("fuel_deducted_from_driver", False))
    fuel_deduction = fuel_total if fuel_deducted else Decimal("0.00")

    anticipado = (
        recaudacion_neta - tpv_visa_total - freenow_app - uber_total_payment
        - other_expenses_total - fuel_deduction
    )

    # 9. Cash = recaudacion_neta - tpv_visa - freenow_app - uber_total_payment
    cash = recaudacion_neta - tpv_visa_total - freenow_app - uber_total_payment

    # 10. Liquidacion = parte_proporcional - anticipado
    liquidacion = parte_proporcional - anticipado

    return {
        "prima_amount": prima_amount,
        "freenow_fixed_bruto": freenow_fixed_bruto,
        "freenow_adjustments": freenow_adjustments,
        "freenow_fixed": freenow_fixed,
        "uber_t3_fixed": uber_t3_fixed,
        "recaudacion_total": recaudacion_total,
        "incidents_amount": incidents_amount,
        "recaudacion_neta": recaudacion_neta,
        "iva": iva,
        "base_imponible": base_imponible,
        "driver_pct": driver_pct,
        "parte_proporcional": parte_proporcional,
        "tpv_visa_total": tpv_visa_total,
        "freenow_app": freenow_app,
        "uber_total_payment": uber_total_payment,
        "fuel_total": fuel_total,
        "other_expenses_total": other_expenses_total,
        "cash": cash,
        "anticipado": anticipado,
        "liquidacion": liquidacion,
    }
