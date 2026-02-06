"""Parse La Caixa VISA Excel export into normalized payment dicts."""
import re
from datetime import datetime
from decimal import Decimal
from openpyxl import load_workbook


def detect_lacaixa_file(filepath: str) -> bool:
    """Detect if file is a La Caixa VISA export."""
    if not filepath.endswith(".xlsx"):
        return False
    try:
        wb = load_workbook(filepath, read_only=True, data_only=True)
        sheet = wb.active
        first_cell = sheet.cell(1, 1).value
        wb.close()
        return first_cell and "Llistat d'operacions" in str(first_cell)
    except Exception:
        return False


def parse_lacaixa_xlsx(filepath: str) -> list[dict]:
    """Parse La Caixa VISA Excel export.

    Format:
    - Row 1: "Llistat d'operacions"
    - Row 3: Account info with license (e.g., "351269212 TAXI LIC. 1061")
    - Row 5: Headers
    - Row 6+: Data rows
    """
    wb = load_workbook(filepath, read_only=True, data_only=True)
    sheet = wb.active

    # Extract license from row 3
    license_row = str(sheet.cell(3, 1).value or "")
    license_match = re.search(r"LIC\.?\s*(\d+)", license_row, re.IGNORECASE)
    license_num = license_match.group(1) if license_match else None

    records = []
    for row in sheet.iter_rows(min_row=6, values_only=True):
        if not row[0]:  # Skip empty rows
            continue

        # Parse datetime (format: "2026-02-03T10:54:42.618")
        dt_str = str(row[0])
        try:
            dt = datetime.fromisoformat(dt_str.split(".")[0])
        except ValueError:
            continue

        # Parse amount (format: "28,00 EUR")
        amount_str = str(row[5] or "0").replace(" EUR", "").replace(",", ".")
        try:
            amount = Decimal(amount_str)
        except Exception:
            continue

        # Extract card last 4 (format: "************3386")
        card_full = str(row[2] or "")
        card_last4 = card_full[-4:] if len(card_full) >= 4 else card_full

        records.append({
            "date": dt.date(),
            "time": dt.time(),
            "terminal_id": str(row[1] or ""),
            "card_last4": card_last4,
            "brand": str(row[3] or "VISA"),
            "amount": amount,
            "status": str(row[6] or ""),
            "_license": license_num,
        })

    wb.close()
    return records
