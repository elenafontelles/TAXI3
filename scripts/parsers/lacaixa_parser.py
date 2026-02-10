"""Parse La Caixa bank statement XLSX into daily TPV totals."""
from __future__ import annotations
import re
from datetime import datetime, date
from decimal import Decimal
from openpyxl import load_workbook

# Terminal prefix (first 2 digits) to license number mapping
TERMINAL_LICENSE_MAP = {
    "34": "092",
    "35": "1061",
    "36": "361",
}


def detect_lacaixa_file(filepath: str) -> bool:
    """Detect if file is a La Caixa bank statement extract."""
    if not filepath.endswith(".xlsx"):
        return False
    try:
        wb = load_workbook(filepath, read_only=True, data_only=True)
        sheet = wb.active
        first_cell = sheet.cell(1, 1).value
        wb.close()
        return first_cell and "Moviments del compte" in str(first_cell)
    except Exception:
        return False


def _parse_date(value) -> date | None:
    """Parse a cell value into a date object."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        return None
    s = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_amount(value) -> Decimal | None:
    """Parse an amount value, handling comma decimals and EUR suffix."""
    if value is None:
        return None
    s = str(value).strip().replace(" EUR", "").replace("\xa0", "")
    # Handle comma as decimal separator (European format)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return Decimal(s).quantize(Decimal("0.01"))
    except Exception:
        return None


def parse_lacaixa_xlsx(filepath: str) -> list[dict]:
    """Parse La Caixa bank statement XLSX extract.

    Format:
    - Row 1: Title ("Moviments del compte...")
    - Row 3: Headers (Data, Data valor, Moviment, Mes dades, Import, Saldo)
    - Row 4+: Data rows

    Filters rows where "Moviment" starts with ON34, ON35 or ON36.
    Maps ON prefixes to license numbers.

    Returns a list of dicts with date, license_number, amount.
    """
    wb = load_workbook(filepath, read_only=True, data_only=True)
    sheet = wb.active

    # Read headers from row 3 to determine column positions
    headers = {}
    for col in range(1, (sheet.max_column or 6) + 1):
        val = sheet.cell(3, col).value
        if val:
            headers[str(val).strip().lower()] = col

    # Determine column indices (fallback to known positions)
    col_date = headers.get("data", 1)
    col_moviment = headers.get("moviment", 3)
    col_import = headers.get("import", 5)

    records = []
    for row in sheet.iter_rows(min_row=4, values_only=False):
        moviment_val = row[col_moviment - 1].value if col_moviment <= len(row) else None
        if not moviment_val:
            continue

        moviment_str = str(moviment_val).strip()

        # Match ON or C. entries (TPV card payments and corrections)
        # Format: "ON 363460767 DDMM" or "C. 363460767 DDMM"
        # The first 2 digits of the terminal number determine the license
        license_number = None
        if moviment_str.startswith("ON ") or moviment_str.startswith("C. "):
            parts = moviment_str.split()
            if len(parts) >= 2:
                terminal = parts[1]
                prefix_2 = terminal[:2]
                license_number = TERMINAL_LICENSE_MAP.get(prefix_2)

        if not license_number:
            continue

        # Parse date
        date_val = row[col_date - 1].value if col_date <= len(row) else None
        day = _parse_date(date_val)
        if not day:
            continue

        # Parse amount
        import_val = row[col_import - 1].value if col_import <= len(row) else None
        amount = _parse_amount(import_val)
        if amount is None or amount == 0:
            continue

        records.append({
            "date": day,
            "license_number": license_number,
            "amount": abs(amount),
        })

    wb.close()
    return records
