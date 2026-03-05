# Contexto de sesion TAXI2 - 10/02/2026

## Proyecto

- **Repo**: `/Users/elenafontelles/TAXI2` (GitHub: `ivantintore/TAXI2`)
- **Stack**: FastAPI + SQLAlchemy + PostgreSQL + Alembic + Docker
- **Produccion**: `https://keonycs.com/tools3/taxi/`
- **Deploy**: GitHub Actions (push a main -> tests -> build Docker -> SSH deploy VPS)
- **Python local**: 3.9 (algunos tests con `str | None` fallan localmente, en CI usa 3.11)

---

## Estado actual

### Ultimo commit pusheado: `7ffb95e`
```
fix: FreeNow commission formula - 12.5% direct, not embedded
```

### Deploy pendiente de verificar
El commit `7ffb95e` fue pusheado y deberia estar desplegado. Verificar con:
```
curl https://keonycs.com/tools3/taxi/health
```

### Lo que la usuaria debe verificar tras deploy
1. **Liquidacion de TAMARA ROSA GOMEZ (vehiculo 0397MSS, licencia 361)**
   - Periodo: 18/12/2025 al 31/12/2025
   - FreenowT3 debe mostrar importes **netos** (no brutos)
   - AppFN debe mostrar importes **netos**
   - Prima debe mostrar los importes correctos (como antes del fix timezone)
   - Valores esperados FreenowT3: 23/12=41.70, 24/12=69.00, 25/12=102.30, 28/12=79.27, 30/12=70.40
   - Valores esperados AppFN: 23/12=31.40, 24/12=46.80, 25/12=60.70, 28/12=118.40, 30/12=111.40

2. **Formulario "Otros gastos"** en la pestana "Subir CSV"
   - Nuevo formulario manual: conductor, fecha (DD/MM/YY), importe, concepto
   - En liquidacion aparece detalle de otros gastos debajo de la tabla principal

---

## Cambios realizados en esta sesion (cronologico)

### 1. Upsert en todos los uploads
- **Archivos**: `src/routes/upload.py`
- Los 4 handlers (trips, fuel, uber, lacaixa) ahora actualizan registros existentes en vez de saltarlos
- Claves de upsert:
  - Trips: `external_id + source`
  - Fuel: `date + vehicle_id + amount + provider`
  - Uber: `date + license_number`
  - La Caixa: `date + license_number`

### 2. FreeNow matching por placa
- **Archivos**: `src/routes/upload.py`
- Resolucion bidireccional driver<->vehicle via `driver_id_to_vehicle` y `vehicle_id_to_driver`
- Fallback: si driver encontrado pero vehicle no -> resolver via license; y viceversa

### 3. Migracion 006: Correccion license-plate mappings
- **Archivos**: `migrations/versions/006_fix_license_plate_mappings.py`
- Mappings correctos: 361-0397MSS, 092-8921LYW, 1061-2965MMM

### 4. Separar queries Prima/FreeNow por manejo de fechas
- **Archivos**: `src/routes/liquidacion.py`
- Prima: usa `func.date(Trip.started_at) == current` (datetimes naivos, hora local)
- FreeNow: usa rango timezone-aware `Europe/Madrid` (datetimes con zona horaria)
- **Razon**: Prima almacena datetimes naivos (hora local sin TZ), FreeNow almacena ISO 8601 con TZ

### 5. La Caixa parser: fecha de descripcion DDMM
- **Archivos**: `scripts/parsers/lacaixa_parser.py`
- Extrae fecha de los ultimos 4 digitos de la descripcion (ej: "ON 340229632 2712" -> dia 27, mes 12)
- Ano tomado de la columna "Data"

### 6. FreeNow neto en recaudacion
- **Archivos**: `src/services/settlement_calculator.py`, `src/routes/liquidacion.py`
- Cuando `freenow_commission_driver_pct > 0`: recaudacion usa importe neto (descontando comision)
- La comision de Tamara esta configurada a 100% en admin

### 7. Template: mostrar freenow_fixed (neto) en vez de freenow_fixed_bruto
- **Archivos**: `src/templates/liquidacion.html`, `src/services/excel_exporter.py`, `src/services/pdf_exporter.py`
- La columna FreeNow mostraba siempre el bruto; ahora muestra `freenow_fixed` (neto si aplica)

### 8. UI: reordenar columnas liquidacion
- **Archivos**: `src/templates/liquidacion.html`
- Orden: Fecha | Prima | Inc | FreenowT3 | Uber T3 | Rec.Neta | IVA | Base Imp. | % | Parte Prop. | TPV/VISA | App FN | App Uber | Gasolina | Otros | Anticipado | Liquidacion
- Eliminada columna "Rec.TOTAL" (redundante, Rec.Neta = Prima - Inc + FreenowT3 + UberT3)

### 9. Entrada manual de otros gastos
- **Archivos**: `src/routes/upload.py`, `src/templates/upload.html`, `src/routes/liquidacion.py`, `src/templates/liquidacion.html`
- POST `/upload/otros-gastos`: guarda OtherExpense (fecha DD/MM/YY, importe, concepto, conductor)
- Liquidacion muestra detalle de otros gastos debajo de la tabla principal

### 10. Correccion formula comision FreeNow
- **Archivos**: `src/services/settlement_calculator.py`, `tests/unit/test_settlement_calculator.py`
- **Antes (mal)**: `commission = bruto - (bruto / 1.125)` -> comision efectiva 11.11%, factor neto 86.56%
- **Ahora (bien)**: `commission = bruto * 0.125` -> comision 12.5%, luego `* 1.21` IVA, factor neto 84.875%
- Formula: `net = bruto - (bruto * 12.5% * 1.21)`

---

## Configuracion clave de conductores

| Conductor | Licencia | Matricula | freenow_commission_driver_pct |
|-----------|----------|-----------|-------------------------------|
| TAMARA ROSA GOMEZ | 361 | 0397MSS | 100% (paga conductor) |
| (otros) | 092, 1061 | 8921LYW, 2965MMM | 0% (paga propietario) |

---

## Arquitectura de liquidacion

### Formula de calculo (`src/services/settlement_calculator.py`)
```
1. freenow_fixed = calculate_freenow_net(bruto) si commission_driver_pct > 0, sino bruto
2. recaudacion_total = prima + freenow_fixed + uber_t3_fixed
3. recaudacion_neta = recaudacion_total - incidencias
4. iva = recaudacion_neta - (recaudacion_neta / 1.1)   [10% IVA]
5. base_imponible = recaudacion_neta - iva
6. driver_pct = bonus_pct si recaudacion_neta >= threshold, sino base_pct
7. parte_proporcional = base_imponible * driver_pct / 100
8. freenow_app = calculate_freenow_net(app_bruto) si commission > 0, sino app_bruto
9. anticipado = recaudacion_neta - tpv_visa - freenow_app - uber_payment - otros - gasolina(si aplica)
10. liquidacion = parte_proporcional - anticipado
```

### Formula comision FreeNow (`calculate_freenow_net`)
```
commission = bruto * 12.5%
commission_with_vat = commission * 1.21
net = bruto - commission_with_vat
net = bruto * 0.84875
```

### Queries de datos diarios (`src/routes/liquidacion.py`)
- **Prima trips**: `func.date(Trip.started_at) == current` + `source="prima"` (datetimes naivos)
- **FreeNow trips**: rango timezone-aware Europe/Madrid + `source="freenow"`
- **FreeNow FIXED**: `fare_type != "METERED"` (incluye FIXED y NULL)
- **FreeNow APP**: `fare_type != "METERED" AND payment_method IN ("APP", "tarjeta")`
- **Incidencias**: trips prima con `distance_km == 0 AND duration_minutes < 0.5`
- **Uber**: `UberDailySummary` por `date + license_number` (o vehicle_id)
- **TPV/VISA**: `TpvDailyTotal` por `date + license_number` (o vehicle_id)
- **Gasolina**: `FuelExpense` por `date + vehicle_id`
- **Otros gastos**: `OtherExpense` por `date + driver_id`

---

## Archivos clave

| Archivo | Descripcion |
|---------|-------------|
| `src/routes/liquidacion.py` | Ruta de liquidacion, queries de datos |
| `src/services/settlement_calculator.py` | Logica de calculo pura |
| `src/routes/upload.py` | Upload de archivos CSV/XLSX + entrada manual otros gastos |
| `src/routes/admin.py` | Admin: editar conductores, vehiculos |
| `src/templates/liquidacion.html` | Template de liquidacion |
| `src/templates/upload.html` | Template de subida |
| `src/services/excel_exporter.py` | Exportador Excel |
| `src/services/pdf_exporter.py` | Exportador PDF |
| `scripts/parsers/freenow_parser.py` | Parser FreeNow CSV |
| `scripts/parsers/prima_parser.py` | Parser Prima CSV |
| `scripts/parsers/lacaixa_parser.py` | Parser La Caixa XLSX (extracto bancario) |
| `scripts/parsers/uber_parser.py` | Parser Uber XLSX |
| `src/models/driver.py` | Modelo Driver (config comisiones) |
| `src/models/trip.py` | Modelo Trip |
| `src/models/other_expense.py` | Modelo OtherExpense |
| `src/models/tpv_daily_total.py` | Modelo TpvDailyTotal |
| `src/models/uber_daily_summary.py` | Modelo UberDailySummary |
| `tests/unit/test_settlement_calculator.py` | Tests de calculo |

---

## Tests

Ejecutar tests compatibles con Python 3.9 local:
```bash
cd /Users/elenafontelles/TAXI2
.venv/bin/python -m pytest tests/unit/test_settlement_calculator.py tests/unit/test_lacaixa_parser.py tests/unit/test_freenow_parser.py tests/unit/test_uber_parser.py -v
```
(Los tests que importan modelos con `str | None` fallan en 3.9 pero pasan en CI con 3.11)

---

## Pendiente / posibles siguientes pasos

1. **Verificar deploy**: confirmar que FreenowT3 y AppFN muestran netos correctos para Tamara
2. **Verificar Prima**: confirmar que importes Prima vuelven a ser correctos
3. **Probar formulario otros gastos**: entrar un gasto manual y verificar que aparece en liquidacion
4. **Otros conductores**: verificar que 092 y 1061 (con commission=0%) siguen mostrando bruto correctamente
