"""Export settlement data to Excel format."""
from io import BytesIO
from decimal import Decimal
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter


def export_settlement_to_excel(
    driver_name: str,
    start_date: str,
    end_date: str,
    results: list[dict],
    totals: dict,
) -> BytesIO:
    """Generate Excel file from settlement data.

    Returns BytesIO buffer containing the Excel file.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Liquidacion"

    # Header
    ws["A1"] = f"Liquidacion: {driver_name}"
    ws["A2"] = f"Periodo: {start_date} - {end_date}"
    ws["A1"].font = Font(bold=True, size=14)

    # Column headers
    headers = [
        "Fecha", "Prima", "FreeNow", "Uber T3", "Rec. TOTAL",
        "Incidencias", "Rec. Neta", "IVA", "Base Imp.", "%",
        "Parte Prop.", "TPV/VISA", "App FN", "App Uber",
        "Gasolina", "Otros", "Anticipado", "Liquidacion",
    ]

    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # Data rows
    row = 5
    for r in results:
        ws.cell(row=row, column=1, value=r["date"].strftime("%d/%m/%Y"))
        ws.cell(row=row, column=2, value=float(r.get("prima_amount", 0)))
        ws.cell(row=row, column=3, value=float(r.get("freenow_fixed", 0)))
        ws.cell(row=row, column=4, value=float(r.get("uber_t3_fixed", 0)))
        ws.cell(row=row, column=5, value=float(r.get("recaudacion_total", 0)))
        ws.cell(row=row, column=6, value=float(r.get("incidents_amount", 0)))
        ws.cell(row=row, column=7, value=float(r.get("recaudacion_neta", 0)))
        ws.cell(row=row, column=8, value=float(r.get("iva", 0)))
        ws.cell(row=row, column=9, value=float(r.get("base_imponible", 0)))
        ws.cell(row=row, column=10, value=float(r.get("driver_pct", 0)))
        ws.cell(row=row, column=11, value=float(r.get("parte_proporcional", 0)))
        ws.cell(row=row, column=12, value=float(r.get("tpv_visa_total", 0)))
        ws.cell(row=row, column=13, value=float(r.get("freenow_app", 0)))
        ws.cell(row=row, column=14, value=float(r.get("uber_total_payment", 0)))
        ws.cell(row=row, column=15, value=float(r.get("fuel_total", 0)))
        ws.cell(row=row, column=16, value=float(r.get("other_expenses_total", 0)))
        ws.cell(row=row, column=17, value=float(r.get("anticipado", 0)))
        ws.cell(row=row, column=18, value=float(r.get("liquidacion", 0)))

        # Format numbers
        for col in range(2, 19):
            ws.cell(row=row, column=col).number_format = '#,##0.00'

        row += 1

    # Totals row
    total_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    ws.cell(row=row, column=1, value="TOTAL").font = Font(bold=True)

    total_cols = {
        2: "prima_amount", 3: "freenow_fixed", 4: "uber_t3_fixed",
        5: "recaudacion_total", 6: "incidents_amount", 7: "recaudacion_neta",
        8: "iva", 9: "base_imponible", 11: "parte_proporcional",
        12: "tpv_visa_total", 13: "freenow_app", 14: "uber_total_payment",
        15: "fuel_total", 16: "other_expenses_total",
        17: "anticipado", 18: "liquidacion",
    }

    for col, key in total_cols.items():
        cell = ws.cell(row=row, column=col, value=float(totals.get(key, 0)))
        cell.fill = total_fill
        cell.font = Font(bold=True)
        cell.number_format = '#,##0.00'

    # Column widths
    col_widths = [12, 10, 10, 10, 12, 12, 12, 10, 10, 6, 12, 10, 10, 10, 10, 10, 12, 12]
    for i, width in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width

    # Save to buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
