"""Parse Petroprix fuel CSV export into normalized expense dicts."""
import csv
from datetime import datetime
from decimal import Decimal


def detect_petroprix_file(filepath: str) -> bool:
    """Detect if file is a Petroprix fuel export."""
    if not filepath.endswith(".csv"):
        return False
    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            header_lower = [h.lower() for h in header]
            return "matricula" in header_lower and "litros" in header_lower
    except Exception:
        return False


def parse_petroprix_csv(filepath: str) -> list[dict]:
    """Parse Petroprix fuel CSV export.

    Petroprix CSVs have a leading empty column and use European decimal format
    (commas as decimal separators), which means numeric values span multiple
    CSV columns. Format: litros=30,82 becomes columns [30, 82] meaning 30.82.

    Returns a list of dicts ready for FuelExpense model creation.
    """
    records = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, [])

        # Find column indices (accounting for leading empty column)
        header_lower = [h.lower().strip() for h in header]

        try:
            fecha_idx = header_lower.index("fecha")
            matricula_idx = header_lower.index("matricula")
            direccion_idx = header_lower.index("direccion")
            litros_idx = header_lower.index("litros")
            importe_idx = header_lower.index("importe_cob")
            tipo_pago_idx = header_lower.index("tipo_pago")
        except ValueError:
            return []

        for row in reader:
            if len(row) <= tipo_pago_idx:
                continue

            date_str = row[fecha_idx].strip()
            if not date_str:
                continue

            try:
                dt = datetime.strptime(date_str, "%d-%m-%Y %H:%M:%S")
            except ValueError:
                continue

            # Handle European decimal format: litros column contains integer part,
            # next column contains decimal part. Same for importe_cob.
            # Example row: ...,30,82,40,00,1,Tarjeta
            # where litros=30.82, importe=40.00, km=1, tipo_pago=Tarjeta
            try:
                # litros is at litros_idx, decimal part at litros_idx+1
                liters_int = row[litros_idx].strip()
                liters_dec = row[litros_idx + 1].strip()
                liters_str = f"{liters_int}.{liters_dec}"
                liters = Decimal(liters_str)

                # importe_cob is at importe_idx, but due to litros having 2 columns,
                # importe is shifted by 1: importe_idx+1, decimal at importe_idx+2
                amount_int = row[importe_idx + 1].strip()
                amount_dec = row[importe_idx + 2].strip()
                amount_str = f"{amount_int}.{amount_dec}"
                amount = Decimal(amount_str)
            except (IndexError, ValueError):
                continue

            # tipo_pago is shifted by 2 due to the extra decimal columns
            # Original header: ..., litros, importe_cob, km, tipo_pago
            # Actual data:     ..., litros_int, litros_dec, importe_int, importe_dec, km, tipo_pago
            # litros adds 1 extra, importe adds 1 extra = 2 total shift
            tipo_pago_actual_idx = tipo_pago_idx + 2
            if len(row) > tipo_pago_actual_idx:
                tipo_pago = row[tipo_pago_actual_idx].strip()
            else:
                tipo_pago = ""

            payment = "tarjeta" if "tarjeta" in tipo_pago.lower() else "efectivo"

            records.append({
                "date": dt.date(),
                "datetime": dt,
                "liters": liters,
                "amount": amount,
                "provider": "petroprix",
                "payment_method": payment,
                "_plate": row[matricula_idx].strip(),
                "_address": row[direccion_idx].strip(),
            })

    return records
