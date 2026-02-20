"""Parse Uber payments CSV export into daily summary dicts per driver."""
from __future__ import annotations
import csv
import re
from collections import defaultdict
from datetime import datetime, date
from decimal import Decimal


def detect_uber_file(filepath: str) -> bool:
    """Detect if file is an Uber payments CSV export."""
    if not filepath.lower().endswith(".csv"):
        return False
    try:
        with open(filepath, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return False
            header_lower = [h.strip().lower() for h in header]
            return (
                "uuid del conductor" in header_lower
                and "importe que se te ha pagado" in header_lower
            )
    except Exception:
        return False


def _parse_decimal(value: str) -> Decimal:
    """Parse a string value into Decimal."""
    if not value or not value.strip():
        return Decimal("0.00")
    s = value.strip().replace(",", ".")
    try:
        return Decimal(s).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")


def _parse_date_from_timestamp(ts: str) -> date | None:
    """Extract date from Uber timestamp like '2026-01-29 08:01:15.836 +0100 CET'."""
    if not ts or not ts.strip():
        return None
    # Extract just the date part (first 10 chars: YYYY-MM-DD)
    m = re.match(r"(\d{4}-\d{2}-\d{2})", ts.strip())
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def parse_uber_csv(filepath: str) -> list[dict]:
    """Parse Uber payments CSV into daily summaries per driver.

    Reads per-trip rows, filters out non-trip rows (so.payout, etc.),
    and aggregates daily totals per driver.

    Key columns:
    - Col C+D: Driver first name + last name
    - Col F: Descripcion (filter: only rows containing 'trip')
    - Col I: Timestamp (for date extraction)
    - Col J: Importe que se te ha pagado -> total_payment
    - Col K: Tus ganancias -> used for t3_fixed calculation
    - Col U: Taximetro -> subtracted from ganancias for t3_fixed

    Returns list of dicts with:
        date, _driver_name, t3_fixed, total_payment, total_earnings, taximeter
    """
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return []

        # Build column index from header names
        header_map = {}
        for i, h in enumerate(header):
            header_map[h.strip()] = i

        # Column indices (0-based)
        col_nombre = header_map.get("Nombre del conductor")
        col_apellido = header_map.get("Apellido del conductor")
        col_desc = header_map.get("Descripción") or header_map.get("Descripcion")
        col_timestamp = header_map.get("en comparación con los informes")
        col_pagado = header_map.get("Importe que se te ha pagado")
        col_ganancias = header_map.get("Importe que se te ha pagado : Tus ganancias")
        col_taximetro = header_map.get(
            "Importe que se te ha pagado:Tus ganancias:Precio:Taxímetro"
        ) or header_map.get(
            "Importe que se te ha pagado:Tus ganancias:Precio:Taximetro"
        )

        if col_pagado is None or col_ganancias is None:
            return []

        # Aggregate daily totals per driver
        # Key: (date, driver_name) -> {t3_fixed, total_payment, total_earnings, taximeter}
        daily = defaultdict(lambda: {
            "t3_fixed": Decimal("0.00"),
            "total_payment": Decimal("0.00"),
            "total_earnings": Decimal("0.00"),
            "taximeter": Decimal("0.00"),
        })

        for row in reader:
            if len(row) <= max(filter(None, [col_pagado, col_ganancias, col_desc, col_timestamp]), default=0):
                continue

            # Filter: only trip rows (skip so.payout, etc.)
            desc = row[col_desc].strip() if col_desc is not None and col_desc < len(row) else ""
            if "trip" not in desc.lower():
                continue

            # Extract date
            ts = row[col_timestamp] if col_timestamp is not None and col_timestamp < len(row) else ""
            day = _parse_date_from_timestamp(ts)
            if not day:
                continue

            # Extract driver name
            nombre = row[col_nombre].strip() if col_nombre is not None and col_nombre < len(row) else ""
            apellido = row[col_apellido].strip() if col_apellido is not None and col_apellido < len(row) else ""
            driver_name = f"{nombre} {apellido}".strip()
            if not driver_name:
                continue

            # Parse amounts
            ganancias = _parse_decimal(row[col_ganancias] if col_ganancias < len(row) else "")
            taximetro_val = Decimal("0.00")
            if col_taximetro is not None and col_taximetro < len(row):
                taximetro_val = _parse_decimal(row[col_taximetro])
            pagado = _parse_decimal(row[col_pagado] if col_pagado < len(row) else "")

            # t3_fixed per trip = ganancias - taximetro
            t3_per_trip = ganancias - taximetro_val

            key = (day, driver_name)
            daily[key]["t3_fixed"] += t3_per_trip
            daily[key]["total_payment"] += pagado
            daily[key]["total_earnings"] += ganancias
            daily[key]["taximeter"] += taximetro_val

    # Convert to list of dicts
    records = []
    for (day, driver_name), totals in sorted(daily.items()):
        records.append({
            "date": day,
            "_driver_name": driver_name,
            "t3_fixed": totals["t3_fixed"].quantize(Decimal("0.01")),
            "total_payment": totals["total_payment"].quantize(Decimal("0.01")),
            "total_earnings": totals["total_earnings"].quantize(Decimal("0.01")),
            "taximeter": totals["taximeter"].quantize(Decimal("0.01")),
        })

    return records
