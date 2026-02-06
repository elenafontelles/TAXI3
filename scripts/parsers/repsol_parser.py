"""Parse Repsol/Solred fuel PDF invoices into normalized expense dicts."""
import re
from datetime import date
from decimal import Decimal


def detect_repsol_file(filepath: str) -> bool:
    """Detect if file is a Repsol/Solred PDF invoice.

    Returns True if file is a PDF and contains SOLRED or Repsol text.
    """
    if not filepath.lower().endswith(".pdf"):
        return False

    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            if not pdf.pages:
                return False
            # Check first page for Repsol/Solred indicators
            text = pdf.pages[0].extract_text() or ""
            text_upper = text.upper()
            return "SOLRED" in text_upper or "REPSOL" in text_upper
    except Exception:
        return False


def _parse_spanish_decimal(value: str) -> Decimal:
    """Parse Spanish decimal format (comma as decimal separator)."""
    # Remove any thousands separators (dots) and convert comma to dot
    cleaned = value.strip().replace(".", "").replace(",", ".")
    return Decimal(cleaned)


def _extract_year_from_pdf(pdf) -> int:
    """Extract the year from the invoice date range."""
    # Look for "Fecha de operación DD/MM/YYYY AL DD/MM/YYYY" pattern
    for page in pdf.pages:
        text = page.extract_text() or ""
        # Pattern: "01/01/2026 AL 31/01/2026" or similar
        match = re.search(r"\d{2}/\d{2}/(\d{4})\s*AL\s*\d{2}/\d{2}/\d{4}", text)
        if match:
            return int(match.group(1))
        # Alternative pattern with just date
        match = re.search(r"Fecha.*?(\d{2}/\d{2}/\d{4})", text)
        if match:
            return int(match.group(1).split("/")[2])
    # Default to current year if not found
    return date.today().year


def parse_repsol_pdf(filepath: str) -> list[dict]:
    """Parse Repsol/Solred fuel PDF invoice.

    Extracts fuel transactions from the detailed operations pages.
    Returns a list of dicts ready for FuelExpense model creation.
    """
    import pdfplumber

    records = []

    with pdfplumber.open(filepath) as pdf:
        year = _extract_year_from_pdf(pdf)

        # Process each page looking for transaction tables
        current_plate = None
        current_driver = None

        for page in pdf.pages:
            text = page.extract_text() or ""

            # Find plate and driver sections in the page
            # Pattern: "Nº de Tarjeta ... Nº de Matrícula XXXXYYYY Conductor NAME"
            # Process line by line to avoid matching across lines
            plate_sections = []
            for line in text.split("\n"):
                match = re.search(
                    r"Nº de Matrícula\s+(\d{4}[A-Z]{3})\s+Conductor\s*([A-Z ]*)?$",
                    line
                )
                if match:
                    plate_sections.append(match)

            # Extract tables from the page
            tables = page.extract_tables()

            if not tables:
                continue

            # For each table, determine which plate section it belongs to
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue

                # Get the plate/driver for this table section
                if table_idx < len(plate_sections):
                    current_plate = plate_sections[table_idx].group(1)
                    driver_match = plate_sections[table_idx].group(2)
                    current_driver = driver_match.strip() if driver_match else None
                elif plate_sections:
                    # Use the last plate section if no direct match
                    current_plate = plate_sections[-1].group(1)
                    driver_match = plate_sections[-1].group(2)
                    current_driver = driver_match.strip() if driver_match else None

                if not current_plate:
                    continue

                # Process table rows
                for row in table[1:]:  # Skip header row
                    if not row or all(cell is None for cell in row):
                        continue

                    # Rows may have merged data with newlines
                    # Get the key columns: Fecha/Hora (col 1), Cantidad (col 5), Importe Total (col 14)
                    try:
                        fecha_hora = row[1] if len(row) > 1 else None
                        cantidad = row[5] if len(row) > 5 else None
                        importe_total = row[14] if len(row) > 14 else None

                        if not fecha_hora or not cantidad or not importe_total:
                            continue

                        # Handle multi-line cells (multiple transactions merged)
                        fechas = str(fecha_hora).split("\n")
                        cantidades = str(cantidad).split("\n")
                        importes = str(importe_total).split("\n")

                        # Process each line as a separate transaction
                        for i, fecha_str in enumerate(fechas):
                            fecha_str = fecha_str.strip()
                            if not fecha_str:
                                continue

                            # Parse date: "DD/MMHH:SS" or "DD/MM HH:SS"
                            date_match = re.match(r"(\d{2})/(\d{2})", fecha_str)
                            if not date_match:
                                continue

                            day = int(date_match.group(1))
                            month = int(date_match.group(2))

                            # Get corresponding liters and amount
                            try:
                                liters_str = cantidades[i].strip() if i < len(cantidades) else None
                                amount_str = importes[i].strip() if i < len(importes) else None

                                if not liters_str or not amount_str:
                                    continue

                                liters = _parse_spanish_decimal(liters_str)
                                amount = _parse_spanish_decimal(amount_str)

                                # Skip rows that are just totals
                                if liters <= 0 or amount <= 0:
                                    continue

                                record = {
                                    "date": date(year, month, day),
                                    "liters": liters,
                                    "amount": amount,
                                    "provider": "repsol",
                                    "payment_method": "tarjeta",
                                    "_plate": current_plate,
                                }

                                if current_driver:
                                    record["_driver"] = current_driver

                                records.append(record)

                            except (ValueError, IndexError, ArithmeticError):
                                continue

                    except (IndexError, TypeError):
                        continue

    return records
