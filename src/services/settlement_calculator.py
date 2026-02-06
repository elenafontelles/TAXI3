"""Calculate driver settlements based on trip data and commission rules."""
from decimal import Decimal, ROUND_HALF_UP


def calculate_freenow_net(bruto: Decimal) -> Decimal:
    """Convert FreeNow bruto amount to net amount with VAT adjustment.

    Formula: bruto / 1.125 * 1.21

    Args:
        bruto: FreeNow gross amount

    Returns:
        Net amount rounded to 2 decimal places
    """
    if bruto == 0:
        return Decimal("0.00")
    result = bruto / Decimal("1.125") * Decimal("1.21")
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
    freenow_bruto: Decimal,
    uber_net: Decimal,
    visa_total: Decimal,
    freenow_app_paid: Decimal,
    uber_app_paid: Decimal,
    freenow_commission: Decimal,
    uber_commission: Decimal,
    driver_config: dict,
) -> dict:
    """Calculate complete daily settlement for a driver.

    Args:
        prima_amount: Prima taxi meter earnings
        freenow_bruto: FreeNow gross amount
        uber_net: Uber net amount
        visa_total: Total VISA payments
        freenow_app_paid: Amount paid through FreeNow app
        uber_app_paid: Amount paid through Uber app
        freenow_commission: FreeNow platform commission
        uber_commission: Uber platform commission
        driver_config: Dict with driver commission settings:
            - commission_base_pct: Base driver percentage
            - commission_bonus_pct: Bonus percentage above threshold
            - commission_threshold: Threshold for bonus percentage
            - freenow_commission_driver_pct: % of FreeNow commission driver pays
            - uber_commission_driver_pct: % of Uber commission driver pays

    Returns:
        Dict with all settlement values:
            - prima_amount, freenow_bruto, freenow_net, uber_net
            - rec_total: Total recognized earnings
            - visa_total, freenow_app_paid, uber_app_paid
            - vat: VAT amount (10%)
            - driver_pct: Applied driver percentage
            - commission_charge: Commission charged to driver
            - driver_share: Driver's share after commission
            - cash: Cash collected by driver
            - debt: Settlement balance (positive = owner owes driver)
    """
    # Calculate FreeNow net from bruto
    freenow_net = calculate_freenow_net(freenow_bruto)

    # Calculate total recognized earnings
    rec_total = prima_amount + freenow_net + uber_net

    # Calculate VAT
    vat = calculate_vat(rec_total)

    # Determine driver percentage
    driver_pct = get_driver_percentage(
        rec_total,
        Decimal(str(driver_config["commission_base_pct"])),
        Decimal(str(driver_config["commission_bonus_pct"])),
        Decimal(str(driver_config["commission_threshold"])),
    )

    # Calculate commission charge to driver
    freenow_driver_pct = Decimal(str(driver_config["freenow_commission_driver_pct"]))
    uber_driver_pct = Decimal(str(driver_config["uber_commission_driver_pct"]))
    commission_charge = (
        freenow_commission * freenow_driver_pct / 100 +
        uber_commission * uber_driver_pct / 100
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Calculate driver share (based on base imponible = rec_total - vat)
    base_imponible = rec_total - vat
    driver_share = (
        base_imponible * driver_pct / 100 - commission_charge
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Calculate cash (what driver collected minus electronic payments)
    cash = rec_total - visa_total - freenow_app_paid - uber_app_paid

    # Calculate debt (positive = owner owes driver)
    debt = driver_share - cash

    return {
        "prima_amount": prima_amount,
        "freenow_bruto": freenow_bruto,
        "freenow_net": freenow_net,
        "uber_net": uber_net,
        "rec_total": rec_total,
        "visa_total": visa_total,
        "freenow_app_paid": freenow_app_paid,
        "uber_app_paid": uber_app_paid,
        "vat": vat,
        "driver_pct": driver_pct,
        "commission_charge": commission_charge,
        "driver_share": driver_share,
        "cash": cash,
        "debt": debt,
    }
