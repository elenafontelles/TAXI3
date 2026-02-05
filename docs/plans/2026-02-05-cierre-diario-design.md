# Sistema de Cierre Diario / Liquidación de Conductores

**Fecha:** 2026-02-05
**Estado:** Aprobado
**Enfoque:** A (integrado en app actual)

## Resumen

Sistema para calcular la liquidación quincenal de cada conductor, consolidando datos de múltiples fuentes (Prima, FreeNow, Uber, VISA, combustible) y aplicando las condiciones específicas de cada conductor.

## Objetivos

- Control contable/fiscal: datos ordenados para impuestos y gestoría
- Liquidación quincenal: calcular cuánto debe el conductor al propietario (o viceversa)
- Validación manual: casos ambiguos requieren aprobación del admin antes del cálculo

## Modelo de Datos

### Cambios al modelo `Driver`

```python
# Configuración de liquidación
commission_base_pct: float = 40.0           # % base conductor
commission_bonus_pct: float = 45.0          # % si supera umbral
commission_threshold: float = 300.0         # Umbral en € (0 = siempre fijo)
freenow_commission_driver_pct: float = 0.0  # % comisión FreeNow que paga conductor
uber_commission_driver_pct: float = 0.0     # % comisión Uber que paga conductor
```

### Nueva tabla `PendingValidation`

```python
id: str (UUID)
trip_id: str (FK, nullable)
validation_type: str  # "incident" | "visa_no_match" | "fuel_no_match"
status: str           # "pending" | "valid" | "invalid"
details: JSON         # datos adicionales según tipo
created_at: datetime
resolved_at: datetime (nullable)
resolved_by: str (nullable)
```

### Nueva tabla `VisaPayment`

```python
id: str (UUID)
date: date
time: time
terminal_id: str
card_last4: str
brand: str            # VISA | MASTERCARD
amount: Decimal
trip_id: str (FK, nullable)
tip_amount: Decimal   # diferencia con viaje = propina
source_file: str
vehicle_id: str (FK)
created_at: datetime
```

### Nueva tabla `FuelExpense`

```python
id: str (UUID)
date: date
vehicle_id: str (FK)
driver_id: str (FK, nullable)
liters: Decimal
amount: Decimal
provider: str         # "petroprix" | "repsol"
source_file: str
payment_method: str   # "efectivo" | "tarjeta"
created_at: datetime
```

### Nueva tabla `OtherExpense`

```python
id: str (UUID)
date: date
driver_id: str (FK)
amount: Decimal
description: str
category: str         # "parking" | "lavado" | "peaje" | "otro"
created_at: datetime
```

## Fuentes de Datos

| Columna | Fuente | Método |
|---------|--------|--------|
| Recaudación Prima | CSV Prima | Automático (scraper) |
| Recaudación FreeNow | CSV FreeNow | Automático (scraper) |
| Recaudación Uber | Manual | Formulario entrada |
| Incidencias | Prima | Auto-detectar → cola validación |
| VISAS | Excel La Caixa (.xlsx) | Upload → match por hora ±10min |
| Pagado APP FreeNow | CSV FreeNow | Automático |
| Pagado APP Uber | Manual | Formulario |
| Cash | Calculado | Rec.Total - VISA - Apps |
| Combustible | CSV Petroprix + PDF Repsol | Upload → asignar por matrícula/nombre |
| Otros gastos | Manual | Formulario |

## Parsers de Archivos

### Detección automática

- **La Caixa VISA:** `*.xlsx` con "Llistat d'operacions" en contenido
- **Petroprix:** `*.csv` con columnas `fecha,matricula,litros,importe`
- **Repsol/Solred:** `*.pdf` con "SOLRED" o "Repsol empresas"

### Flujo de importación

1. Detectar tipo de archivo por nombre/contenido
2. Parsear y extraer registros
3. Asignar a vehículo/conductor (por matrícula, si no por nombre)
4. Si no hay match → cola de validación
5. Guardar en tabla correspondiente

## Cola de Validación

### Página `/validacion`

Pestañas:
- **Incidencias** - Viajes sospechosos (0km, <30s, etc.)
- **VISA sin match** - Pagos sin viaje asociado
- **Combustible sin match** - Repostajes sin vehículo/conductor

### Criterios de incidencia (Prima)

- `km = 0` Y `tiempo < 30 segundos` → posible ticket nulo
- Se muestra en cola para que admin decida

### Acciones por item

- **Válido** → se incluye en cálculo
- **Incidencia/Descartar** → se excluye del cálculo
- **Asignar a...** → vincular manualmente a viaje/conductor

### Email automático

- Destinatario: admin
- Trigger: cuando hay ≥1 item pendiente
- Frecuencia: al importar archivos

## Fórmulas de Liquidación

### Cálculo de recaudación neta

```
FreeNow neto = importe_bruto / 1.125 × 1.21
Uber neto = importe (ya viene neto)
Rec. TOTAL = Prima + FreeNow neto + Uber neto
```

### Cálculo de IVA

```
IVA (10%) = Rec.Total - (Rec.Total / 1.1)
```

### Porcentaje del conductor

```
Si Rec.Total >= threshold:
    % = commission_bonus_pct
Sino:
    % = commission_base_pct
```

### Reparto de comisiones de plataformas

```
Comisión FreeNow a cargo conductor = Com.FreeNow × (freenow_commission_driver_pct / 100)
Comisión Uber a cargo conductor = Com.Uber × (uber_commission_driver_pct / 100)
```

### Liquidación final

```
Base imponible = Rec.Total - IVA
Parte conductor = Base imponible × (% / 100) - comisiones a su cargo
Cash anticipado = Rec.Total - VISA - Pagos APP
Deuda a conductor = Parte conductor - Cash anticipado
```

- **Deuda positiva** → propietario debe al conductor
- **Deuda negativa** → conductor debe al propietario

### Gastos

- **Combustible** → a cargo del propietario (no afecta liquidación conductor)
- **Otros gastos** → se introducen manualmente, se restan aparte

## Interfaz de Usuario

### Página `/liquidacion`

**Formulario:**
- Selector de conductor
- Fecha inicio / fecha fin
- Botón "Generar cierre"

**Validación:**
- Aviso si hay items pendientes en cola de validación

**Vista de tabla (estilo Excel):**

| Fecha | Rec. Prima | Rec. FreeNow | Rec. Uber | Rec. TOTAL | Incid. | VISA | Pago APP FN | Pago APP Uber | Cash | Combust. | Otros | IVA | % | Parte Cond. | Anticipado | Deuda |
|-------|------------|--------------|-----------|------------|--------|------|-------------|---------------|------|----------|-------|-----|---|-------------|------------|-------|

**Funcionalidades:**
- Fila con fondo rojo si hay incidencias pendientes
- Click en celda → ver detalle
- Botón "Descargar Excel"
- Botón "Descargar PDF"

### Página `/admin` - Editar conductor

Nueva sección "Condiciones de liquidación":

```
┌─────────────────────────────────────────────────────┐
│ Condiciones de liquidación                          │
├─────────────────────────────────────────────────────┤
│ % base conductor:        [40  ] %                   │
│ % bonificado:            [45  ] %                   │
│ Umbral bonificación:     [300 ] € (0 = siempre fijo)│
│                                                     │
│ Comisión FreeNow - % conductor: [0   ] %            │
│ Comisión Uber - % conductor:    [0   ] %            │
└─────────────────────────────────────────────────────┘
```

## Valores por Defecto

Para nuevos conductores:
- % base: 40%
- % bonificado: 45%
- Umbral: 300€
- Comisión FreeNow conductor: 0%
- Comisión Uber conductor: 0%

## Archivos de Ejemplo

- **La Caixa VISA:** `351269212 01157277 2026-02-03.xlsx`
- **Petroprix:** `repostajes.csv`
- **Repsol/Solred:** `factura (4).pdf`
- **Fórmulas referencia:** `formulas taxi 361.xlsx`
