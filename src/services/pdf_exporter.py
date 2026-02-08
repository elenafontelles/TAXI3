"""Export settlement data to PDF format."""
from io import BytesIO
from decimal import Decimal
from fpdf import FPDF


def export_settlement_to_pdf(
    driver_name: str,
    start_date: str,
    end_date: str,
    results: list[dict],
    totals: dict,
) -> BytesIO:
    """Generate PDF file from settlement data.

    Returns BytesIO buffer containing the PDF file.
    """
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Liquidacion: {driver_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Periodo: {start_date} - {end_date}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Table headers
    headers = [
        ("Fecha", 22),
        ("Prima", 20),
        ("FreeNow", 20),
        ("Uber", 20),
        ("TOTAL", 20),
        ("VISA", 18),
        ("App FN", 20),
        ("App Uber", 22),
        ("Cash", 18),
        ("IVA", 18),
        ("%", 12),
        ("Conductor", 22),
        ("Deuda", 20),
    ]

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(68, 114, 196)
    pdf.set_text_color(255, 255, 255)

    for name, width in headers:
        pdf.cell(width, 7, name, border=1, fill=True, align="C")
    pdf.ln()

    # Data rows
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(0, 0, 0)

    for i, r in enumerate(results):
        if i % 2 == 0:
            pdf.set_fill_color(245, 245, 245)
        else:
            pdf.set_fill_color(255, 255, 255)

        fill = True
        date_str = r["date"].strftime("%d/%m/%Y")

        row_data = [
            date_str,
            _fmt(r.get("prima_amount", 0)),
            _fmt(r.get("freenow_net", 0)),
            _fmt(r.get("uber_net", 0)),
            _fmt(r.get("rec_total", 0)),
            _fmt(r.get("visa_total", 0)),
            _fmt(r.get("freenow_app_paid", 0)),
            _fmt(r.get("uber_app_paid", 0)),
            _fmt(r.get("cash", 0)),
            _fmt(r.get("vat", 0)),
            _fmt(r.get("driver_pct", 0)),
            _fmt(r.get("driver_share", 0)),
            _fmt(r.get("debt", 0)),
        ]

        for j, (_, width) in enumerate(headers):
            align = "L" if j == 0 else "R"
            pdf.cell(width, 6, row_data[j], border=1, fill=fill, align=align)
        pdf.ln()

    # Totals row
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(217, 225, 242)

    total_data = [
        "TOTAL",
        _fmt(totals.get("prima_amount", 0)),
        _fmt(totals.get("freenow_net", 0)),
        _fmt(totals.get("uber_net", 0)),
        _fmt(totals.get("rec_total", 0)),
        _fmt(totals.get("visa_total", 0)),
        _fmt(totals.get("freenow_app_paid", 0)),
        _fmt(totals.get("uber_app_paid", 0)),
        _fmt(totals.get("cash", 0)),
        _fmt(totals.get("vat", 0)),
        "",
        _fmt(totals.get("driver_share", 0)),
        _fmt(totals.get("debt", 0)),
    ]

    for j, (_, width) in enumerate(headers):
        align = "L" if j == 0 else "R"
        pdf.cell(width, 7, total_data[j], border=1, fill=True, align=align)
    pdf.ln()

    # Output
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer


def _fmt(value) -> str:
    """Format a Decimal or number to string with 2 decimal places."""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "0.00"
