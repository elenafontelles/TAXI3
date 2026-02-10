"""Validate CSV/file schema before parsing to catch format changes early."""
import csv
import logging

logger = logging.getLogger(__name__)

# Required columns per platform (case-sensitive as they appear in real files)
REQUIRED_COLUMNS = {
    "freenow": {
        "BOOKING ID", "BOOKING STATE", "TOUR VALUE", "TOUR TIP",
        "TOLL VALUE", "TAX PERCENTAGE", "PICKUP DATE", "CLOSED DATE",
        "PAYMENT METHOD", "FARE TYPE", "DRIVER FIRST NAME", "DRIVER LAST NAME",
        "LICENCE PLATE",
    },
    "prima": {
        "TripNumber", "DateTripStart", "DateTripEnd", "AmountTotalPaid",
        "AmountTips", "AmountTolls", "PaymentMode", "km", "DriverName",
        "License",
    },
    "petroprix": {"fecha", "matricula", "litros", "importe_cob", "tipo_pago"},
}

# Delimiter per platform
DELIMITERS = {
    "freenow": ",",
    "prima": ";",
    "petroprix": ",",
}


def validate_csv_schema(filepath: str, platform: str) -> tuple[bool, str]:
    """Validate that a CSV file contains the required columns for a platform.

    Args:
        filepath: Path to the CSV file
        platform: Platform name (uber, freenow, prima, petroprix)

    Returns:
        Tuple of (is_valid, error_message). error_message is empty if valid.
    """
    required = REQUIRED_COLUMNS.get(platform)
    if required is None:
        return True, ""

    delimiter = DELIMITERS.get(platform, ",")

    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=delimiter)
            header_row = next(reader, None)
    except Exception as e:
        return False, f"No se pudo leer el archivo CSV: {e}"

    if not header_row:
        return False, "El archivo esta vacio o no tiene cabecera"

    # Strip whitespace from headers
    actual = {h.strip() for h in header_row}

    # Case-insensitive check for petroprix (headers may vary case)
    if platform == "petroprix":
        actual_lower = {h.lower() for h in actual}
        required_lower = {r.lower() for r in required}
        missing = required_lower - actual_lower
    else:
        missing = required - actual

    if missing:
        missing_list = ", ".join(sorted(missing))
        logger.warning(f"CSV schema validation failed for {platform}: missing columns {missing_list}")
        return False, f"Columnas requeridas no encontradas: {missing_list}. Verifica que el formato del archivo es correcto."

    return True, ""
