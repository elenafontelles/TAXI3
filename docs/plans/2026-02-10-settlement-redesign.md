# Rediseno del sistema de liquidacion

**Fecha:** 2026-02-10
**Autores:** Elena Fontelles + Claude

---

## Objetivo

Corregir y simplificar el calculo de liquidacion de taxistas, adaptando parsers y logica de negocio a los archivos reales disponibles.

---

## Fuentes de datos

| Fuente | Formato | Frecuencia | Contenido |
|--------|---------|------------|-----------|
| Prima | CSV (;) | Semanal/quincenal/mensual por licencia | Todos los viajes taximetro |
| FreeNow | CSV (,) | Semanal/quincenal/mensual por licencia | Viajes app: FIXED + METERED |
| Uber | XLSX | Semanal/quincenal/mensual por licencia (opcional) | Resumen diario: T3 fija, total pago uber |
| Extracto bancario La Caixa | XLSX | Semanal/quincenal/mensual por cuenta (2 cuentas) | Movimientos bancarios con totales TPV diarios |

---

## Parsers a modificar/crear

### 1. FreeNow parser (corregir)
- `PAYMENT METHOD`: guardar como "CASH" o "APP" (no "efectivo"/"tarjeta")
- Filtrar por `FARE TYPE`: "FIXED" (tarifa fija app) vs "METERED" (taximetro, se ignora)
- Solo viajes FIXED se suman a recaudacion y pagos APP

### 2. Uber parser (rehacer)
- Formato: XLSX (no CSV)
- Columnas: Licencia, Dia, Ganancias totales, Taximetro, Reembolso, Ajustes, Total T3 fija uber, Total pago uber
- Un archivo por licencia, no siempre existe (no todas las licencias trabajan con Uber cada mes)
- "Total T3 fija uber" ya viene neta de taximetro (no hay doble conteo con Prima)

### 3. La Caixa parser (rehacer)
- Formato: XLSX extracto de movimientos de cuenta (no listado VISA individual)
- Nombre tipico: "Moviments_compte_XXXXXXX.xlsx"
- Estructura: Row 1 = titulo cuenta, Row 2 = moneda, Row 3 = headers (Data, Data valor, Moviment, Mes dades, Import, Saldo), Row 4+ = datos
- Filtrar filas TPV por prefijo en columna "Moviment":
  - ON34... → licencia 092
  - ON35... → licencia 1061
  - ON36... → licencia 361
- Extraer fecha + importe de cada fila TPV
- Resultado: total TPV diario por licencia
- Solo 2 archivos al mes (1 por cuenta bancaria: Ivan y Elena)

### 4. Eliminar visa_matcher.py
- Ya no se necesita match individual VISA <-> viaje

---

## Calculo de liquidacion

### Formula completa

```
1. Recaudacion total = Prima + FreeNow FIXED + Uber T3 fija

2. Incidencias = viajes Prima con 0 km y < 30 seg (viajes nulos)

3. Recaudacion neta = recaudacion total - incidencias

4. IVA = 10% de recaudacion neta

5. Base imponible = recaudacion neta - IVA

6. % taxista (segun licencia y recaudacion neta):
   - Lic 092 y 1061: siempre 45%
   - Lic 361: 40%, sube a 45% si recaudacion neta >= 300€

7. Parte proporcional = base imponible x % taxista

8. Anticipado a conductor = recaudacion neta
                          - pagado VISA (TPV del extracto bancario)
                          - pagado app FreeNow (neto o bruto segun licencia)
                          - pagado app Uber (total pago uber del XLSX)
                          - otros gastos
                          - gasolina (solo si fuel_deducted_from_driver = true)

9. Liquidacion = parte proporcional - anticipado a conductor
   -> Positivo = propietario debe al conductor
   -> Negativo = conductor debe al propietario
```

### Comision FreeNow

- Formula neto: bruto / 1.125 * 1.21
- Se aplica segun parametro `freenow_commission_driver_pct`:
  - 0% -> se usa bruto (propietario asume comision)
  - 100% -> se usa neto (comision descontada del importe)

### Configuracion por licencia

| Parametro | 092 | 1061 | 361 |
|-----------|-----|------|-----|
| freenow_commission_driver_pct | 0% | 100% | 100% |
| prima_base_pct | 45% | 45% | 40% |
| prima_bonus_pct | 45% | 45% | 45% |
| commission_threshold | 0 | 0 | 300 |
| fuel_deducted_from_driver | false | false | true |

---

## Cambios en el codigo

### Parsers
1. **Corregir** `scripts/parsers/freenow_parser.py` — payment_method CASH/APP + campo fare_type FIXED/METERED
2. **Rehacer** `scripts/parsers/uber_parser.py` — nuevo formato XLSX con 8 columnas
3. **Rehacer** `scripts/parsers/lacaixa_parser.py` — extracto bancario -> totales TPV diarios por licencia
4. **Eliminar** `src/services/visa_matcher.py` — ya no se necesita

### Modelo Driver
5. **Renombrar** `commission_base_pct` -> `prima_base_pct`
6. **Renombrar** `commission_bonus_pct` -> `prima_bonus_pct`
7. **Anadir** campo `fuel_deducted_from_driver` (boolean, default false)

### Servicio de liquidacion
8. **Rehacer** `src/services/settlement_calculator.py` — nueva formula completa
9. **Actualizar** `src/routes/liquidacion.py` — usar nueva formula, incorporar gastos y gasolina

### Modelo VisaPayment / tabla TPV
10. **Adaptar** o crear nuevo modelo para totales TPV diarios por licencia (en vez de pagos VISA individuales)

### Tests
11. **Actualizar** tests unitarios de parsers, settlement_calculator y liquidacion
