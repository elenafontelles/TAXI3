# 🚕 TAXI API - Sistema de Gestión y Facturación

**La centralización definitiva de datos de taxi multi-plataforma**

> **Propietarios:** J. Iván Tintoré (2 taxis) + Elena Fontelles (1 taxi)
> **Fecha:** 27 Enero 2026
> **Versión:** 1.0

---

## 📚 Índice

1. [Objetivo del Proyecto](#1-objetivo-del-proyecto)
2. [Fuentes de Datos](#2-fuentes-de-datos)
3. [Arquitectura Propuesta](#3-arquitectura-propuesta)
4. [Modelo de Datos](#4-modelo-de-datos-postgresql)
5. [Seguridad](#5-seguridad)
6. [Flujo de Sincronización](#6-flujo-de-sincronización-diaria)
7. [API Contract](#7-api-contract---endpoints-fastapi)
8. [Dashboard y Métricas](#8-dashboard---métricas-clave)
9. [Estructura del Proyecto](#9-estructura-del-proyecto)
10. [Estrategia de Testing](#10-estrategia-de-testing)
11. [Próximos Pasos](#11-próximos-pasos)

---

## 1. Objetivo del Proyecto

Sistema centralizado para consolidar la facturación de **3 taxis** desde múltiples plataformas, con **sincronización diaria automática** y **dashboard de análisis**.

### Objetivos Específicos

| Objetivo | Descripción |
|----------|-------------|
| **Control contable/fiscal** | Datos ordenados para impuestos y gestoría |
| **Análisis de rentabilidad** | Qué plataforma/horarios son más rentables |
| **Dashboard completo** | Visualización en tiempo real del negocio |

---

## 2. Fuentes de Datos

### 2.1 Uber

| Aspecto | Detalle |
|---------|---------|
| **Estado** | ✅ API Disponible (acceso limitado) |
| **Documentación** | [developer.uber.com/docs/drivers](https://developer.uber.com/docs/drivers/introduction) |
| **Autenticación** | OAuth 2.0 (el conductor autoriza la app) |
| **Endpoints principales** | `/partners/me`, `/partners/trips`, `/partners/payments` |

**Datos disponibles:**
- Perfil del conductor (rating, foto, estado activo)
- Viajes: distancia, duración, tarifa, ciudad
- Pagos: moneda, importe, fecha de pago
- Filtros por rango de fechas (`from_time`, `to_time`)

**⚠️ VERIFICACIÓN CRÍTICA REQUERIDA:**
- **Rate Limits**: Consultar documentación oficial sobre límites de peticiones (req/min, req/día)
- **Retención de Datos**: Confirmar ventana de acceso histórico (¿30 días? ¿6 meses? ¿sin límite?)
- **Acceso OAuth**: Validar que el proceso de autorización del conductor funciona correctamente

**Acción requerida:** Registrar app en [developer.uber.com](https://developer.uber.com) para obtener credenciales OAuth y verificar límites.

---

### 2.2 FreeNow

| Aspecto | Detalle |
|---------|---------|
| **Estado** | ✅ Portal con Export CSV |
| **Acceso** | [portal.free-now.com](https://portal.free-now.com/) |
| **Tipo de acceso** | Login de conductor o empresa |

**Funcionalidades del Portal:**
- **Historial de servicios**: Descarga de archivos CSV con ganancias
- **Ingresos**: Información completa de ganancias, gastos, cálculo de salarios
- **Recibos**: Acceso a recibos individuales de cada viaje
- **Dashboard**: Ingresos últimos 7 días + últimos trayectos

**Como titular de licencia** tienes acceso a:
- Toda la facturación
- Actualización de documentos (vehículos, conductores)
- Añadir asalariados
- Modificar vehículos

**⚠️ VERIFICACIÓN CRÍTICA REQUERIDA:**
- **Automatización**: Confirmar si existe API alternativa (aunque no esté documentada públicamente)
- **Contacto Soporte**: Considerar ticket a soporte empresarial/flota para opciones de exportación automática (SFTP, email reports, etc.)
- **Plan B Manual**: Si no hay automatización, seguir este proceso:
  1. Descargar CSV diario desde el portal FreeNow
  2. Renombrar archivo como `freenow_YYYY-MM-DD.csv` (ej: `freenow_2026-01-27.csv`)
  3. Subir archivo a la carpeta `imports/` del servidor
  4. La tarea `sync_freenow_task` lo procesará automáticamente en el siguiente ciclo

**Fuentes:**
- [Portal FreeNow: para qué sirve](https://driver.free-now.com/hc/es/articles/9686164083218-Portal-Freenow-para-qué-sirve-y-cómo-acceder-a-él)
- [Cómo acceder al Portal](https://driver.free-now.com/hc/es/articles/9103216801426-Cómo-acceder-al-Portal-Freenow)

---

### 2.3 Prima (Taxitronic)

| Aspecto | Detalle |
|---------|---------|
| **Estado** | ✅ Plataforma Cloud + Export CSV |
| **Acceso** | Cloud (cualquier dispositivo con internet) |
| **Web** | [taxitronic.com/Control-taxis](https://www.taxitronic.com/Control-taxis/) |

**Datos disponibles (muy completos):**

```
📊 POR TURNO:
- Conductor, fecha/hora inicio y fin
- Tiempo y km recorridos (libre vs ocupado)
- Velocidad máxima
- Importes recaudados

📍 POR SERVICIO (VIAJE):
- Hora inicio y fin
- Importes: carrera, suplementos, propinas, peajes
- Tarifas utilizadas
- Tiempo, distancia, velocidad máxima
- Coordenadas GPS inicio y fin
- Modo de pago
- Alarma de suplementos borrados
```

**Compatibilidad taxímetros:** TXD30+TC50, TV60+TC60 (Gobox), TXD70

**Exportación:** CSV compatible con Excel y cualquier herramienta de datos.

**⚠️ VERIFICACIÓN CRÍTICA REQUERIDA:**
- **Automatización Real**: El término "Automático diario" es una **ASUNCIÓN**. Validar si Prima permite:
  - Exportación programada (SFTP, FTP, API)
  - Descarga vía API sin intervención manual
  - Email automático de datos
- **Si requiere login manual**: Considerar scraping (frágil, rompe con cambios de UI, posible violación ToS)
- **Impacto**: Si no es automático, afecta propuesta de valor del sistema

**Plan de Contingencia (si NO hay automatización):**

|| Escenario | Solución | SLA | Riesgo |
||-----------|----------|-----|--------|
|| **Ideal: API disponible** | Integración directa | Automático 02:05 AM | Ninguno |
|| **Plan B: Export programado** | SFTP/FTP diario | Automático 02:05 AM | Bajo |
|| **Plan C: Export manual** | Proceso documentado abajo | Manual diario | Medio |
|| **Plan D: Scraping** | Selenium/Playwright | Semi-automático | Alto (frágil) |

**Proceso Manual (Plan C):**
1. **Responsable**: Iván (turno mañana) o conductor activo
2. **Horario**: Antes de las 09:00 AM
3. **Pasos**:
   - Login en Prima cloud (credenciales en secrets manager)
   - Navegar a "Exportar datos" → Seleccionar fecha (día anterior)
   - Descargar CSV → Renombrar como `prima_YYYY-MM-DD.csv`
   - Subir a carpeta `imports/` del servidor (vía SFTP o dashboard web)
4. **Validación**: Sistema detecta archivo y lo procesa automáticamente
5. **Alertas**: Si a las 10:00 AM no se detecta archivo → Telegram alert a Iván

**Acción urgente**: Verificar en cloud de Prima o contactar soporte técnico Taxitronic.

---

## 3. Arquitectura Propuesta

### 3.1 Stack Tecnológico

```
┌─────────────────────────────────────────────────────────────┐
│                      TAXI API SYSTEM                         │
├─────────────────────────────────────────────────────────────┤
│  FRONTEND          │  React + Recharts (Dashboard)          │
│  API               │  Python 3.11+ / FastAPI                │
│  DATABASE          │  PostgreSQL 15+                        │
│  SCHEDULER         │  Celery + Redis                        │
│  CONTAINERS        │  Docker + Docker Compose               │
│  DEPLOYMENT        │  VPS propio                            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Diagrama de Arquitectura

```
┌────────────────────────────────────────────────────────────────┐
│                      CAPA DE PRESENTACIÓN                       │
│                    ┌──────────────────────┐                     │
│                    │   DASHBOARD (React)  │                     │
│                    │   + Recharts         │                     │
│                    └──────────┬───────────┘                     │
│                               │ HTTPS                           │
└───────────────────────────────┼─────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────┐
│                      CAPA DE API (Lectura)                      │
│                    ┌──────────▼───────────┐                     │
│                    │   FastAPI Backend    │                     │
│                    │   (JWT Auth)         │                     │
│                    └──────────┬───────────┘                     │
│                               │                                 │
└───────────────────────────────┼─────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────┐
│                    CAPA DE DATOS (Escritura)                    │
│                               │                                 │
│        ┌──────────────────────▼────────────────────┐            │
│        │         PostgreSQL Database                │            │
│        │  (trips, drivers, vehicles, shifts)        │            │
│        └──────────────────────▲────────────────────┘            │
│                               │                                 │
│        ┌──────────────────────┴────────────────────┐            │
│        │         Celery Workers (Sync)              │            │
│        │         + Redis Queue                      │            │
│        └──────┬─────────┬──────────┬────────────────┘            │
│               │         │          │                             │
└───────────────┼─────────┼──────────┼─────────────────────────────┘
                │         │          │
┌───────────────┼─────────┼──────────┼─────────────────────────────┐
│         CONECTORES (Ingesta de Datos)                            │
│               │         │          │                             │
│        ┌──────▼────┐ ┌──▼──────┐ ┌▼──────────┐                  │
│        │   Uber    │ │ FreeNow │ │   Prima   │                  │
│        │ Connector │ │Connector│ │ Connector │                  │
│        └──────┬────┘ └──┬──────┘ └┬──────────┘                  │
│               │         │          │                             │
└───────────────┼─────────┼──────────┼─────────────────────────────┘
                │         │          │
┌───────────────┼─────────┼──────────┼─────────────────────────────┐
│         FUENTES EXTERNAS (Solo Lectura)                          │
│               │         │          │                             │
│        ┌──────▼────┐ ┌──▼──────┐ ┌▼──────────┐                  │
│        │   Uber    │ │ Portal  │ │Taxitronic │                  │
│        │    API    │ │  CSV    │ │   Cloud   │                  │
│        │  (OAuth)  │ │ Manual  │ │  CSV/API  │                  │
│        └───────────┘ └─────────┘ └───────────┘                  │
└────────────────────────────────────────────────────────────────┘

FLUJO DE DATOS:
→ Lectura (Dashboard → FastAPI → PostgreSQL)
← Escritura (Fuentes Externas → Conectores → Celery → PostgreSQL)
```

### 3.3 Conectores por Plataforma

| Plataforma | Método de Obtención | Frecuencia | Estado Verificación |
|------------|---------------------|------------|---------------------|
| **Uber** | API REST con OAuth | Automático diario | ⚠️ Verificar rate limits |
| **FreeNow** | Descarga CSV del Portal | Semi-manual** | ⚠️ Confirmar automatización |
| **Prima** | Export CSV cloud | ❓ Por confirmar | ⚠️ **CRÍTICO**: Verificar si realmente es automático |

**Notas importantes:**
- **FreeNow: Proceso manual documentado en Sección 2.2 con SLA y governance
- ***Prima: "Automático diario" es una ASUNCIÓN no verificada. Plan de contingencia definido en Sección 2.3

---

## 4. Modelo de Datos PostgreSQL

### 4.1 Tabla: `owners` (Propietarios)

```sql
CREATE TABLE owners (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    tax_id          VARCHAR(50) UNIQUE NOT NULL,  -- NIF/CIF
    email           VARCHAR(255),
    phone           VARCHAR(20),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Datos iniciales
-- J. Iván Tintoré (propietario, 2 taxis)
-- Elena Fontelles (propietaria, 1 taxi)
```

### 4.2 Tabla: `drivers` (Conductores)

```sql
CREATE TABLE drivers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(255) UNIQUE,
    phone           VARCHAR(20),
    license_number  VARCHAR(50) UNIQUE NOT NULL,
    owner_id        UUID REFERENCES owners(id) NOT NULL,  -- Propietario del taxi
    is_owner        BOOLEAN DEFAULT FALSE,  -- TRUE si el conductor es también propietario
    
    -- IDs de plataformas (para mapeo driver-plataforma)
    uber_driver_id      VARCHAR(100),
    freenow_driver_id   VARCHAR(100),
    
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Propietarios que también conducen tendrán is_owner=TRUE
-- Conductores asalariados tendrán is_owner=FALSE
```

### 4.3 Tabla: `vehicles` (Vehículos)

```sql
CREATE TABLE vehicles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plate           VARCHAR(20) UNIQUE NOT NULL,
    license_number  VARCHAR(50) NOT NULL,  -- Licencia de taxi (puede no ser única si se transfiere)
    model           VARCHAR(100),
    brand           VARCHAR(50),
    year            INTEGER,
    owner_id        UUID REFERENCES owners(id) NOT NULL,
    taximeter_id    VARCHAR(50),  -- ID del taxímetro Prima
    uber_vehicle_id VARCHAR(100),
    freenow_vehicle_id VARCHAR(100),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para búsquedas frecuentes
CREATE INDEX idx_vehicles_owner ON vehicles(owner_id);
CREATE INDEX idx_vehicles_active ON vehicles(is_active) WHERE is_active = TRUE;
```

### 4.4 Tabla: `trips` (Viajes - TABLA CENTRAL)

```sql
CREATE TABLE trips (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificación
    source          VARCHAR(20) NOT NULL,  -- 'uber', 'freenow', 'prima', 'street'
    external_id     VARCHAR(100),          -- ID original de la plataforma

    -- Relaciones
    driver_id       UUID REFERENCES drivers(id) NOT NULL,
    vehicle_id      UUID REFERENCES vehicles(id) NOT NULL,
    shift_id        UUID REFERENCES shifts(id),

    -- Tiempo
    started_at      TIMESTAMPTZ NOT NULL,
    ended_at        TIMESTAMPTZ,
    duration_minutes DECIMAL(10,2),

    -- Ubicación
    origin_lat      DECIMAL(10,7),
    origin_lng      DECIMAL(10,7),
    dest_lat        DECIMAL(10,7),
    dest_lng        DECIMAL(10,7),
    origin_address  TEXT,
    dest_address    TEXT,

    -- Distancia
    distance_km     DECIMAL(10,2),

    -- Importes (multi-currency support)
    currency_code   CHAR(3) NOT NULL DEFAULT 'EUR',  -- ISO 4217
    gross_amount    DECIMAL(10,2) NOT NULL,  -- Importe bruto total
    commission      DECIMAL(10,2) DEFAULT 0, -- Comisión plataforma
    platform_fee    DECIMAL(10,2) DEFAULT 0, -- Tarifa adicional plataforma
    taxes_vat       DECIMAL(10,2) DEFAULT 0, -- IVA/Impuestos (incluido en gross si aplica)
    tips            DECIMAL(10,2) DEFAULT 0, -- Propinas (incluidas en gross)
    tolls           DECIMAL(10,2) DEFAULT 0, -- Peajes (incluidos en gross)
    adjustments     DECIMAL(10,2) DEFAULT 0, -- Ajustes post-viaje (+ o -, Uber)
    
    -- IMPORTANTE: net_amount NO es columna generada porque la fórmula varía por plataforma
    -- Calcular en consultas como: gross_amount - commission - platform_fee + adjustments
    -- Para payout real del conductor, ver payout_amount
    payout_amount   DECIMAL(10,2),           -- Cantidad real recibida (fuente de verdad)
    exchange_rate   NUMERIC(10,4),           -- Tipo de cambio si currency != EUR
    
    -- Desglose detallado (incentivos, extras, etc.)
    amount_breakdown JSONB DEFAULT '{}',  -- {incentivos, bonos, surcharges...}
    
-- NOTA IMPORTANTE SOBRE IMPORTES:
-- - gross_amount: Total que pagó el pasajero
-- - payout_amount: Total que recibió el conductor (después de comisiones/ajustes)
-- - La diferencia es lo que se queda la plataforma
-- - Para reporting fiscal, usar payout_amount como ingreso real
    
    -- Detalles
    payment_method  VARCHAR(20),         -- 'card', 'cash', 'app'
    tariff_code     VARCHAR(20),         -- Código de tarifa aplicada

    -- Datos originales
    raw_data        JSONB,               -- JSON completo original

    -- Deduplicación entre fuentes
    merged_into_trip_id UUID REFERENCES trips(id),  -- Si es duplicado, referencia al trip canónico
    is_canonical    BOOLEAN DEFAULT TRUE,           -- TRUE si es el registro maestro

    -- Metadata
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Evitar duplicados con external_id (solo cuando no es NULL)
CREATE UNIQUE INDEX idx_unique_trip_external_id
ON trips (source, external_id)
WHERE external_id IS NOT NULL;

-- Índices para consultas frecuentes
CREATE INDEX idx_trips_source ON trips(source);
CREATE INDEX idx_trips_driver ON trips(driver_id);
CREATE INDEX idx_trips_started ON trips(started_at);
CREATE INDEX idx_trips_driver_date ON trips(driver_id, started_at);
CREATE INDEX idx_trips_canonical ON trips(is_canonical) WHERE is_canonical = TRUE;
```

### 4.5 Tabla: `shifts` (Turnos)

```sql
CREATE TABLE shifts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id       UUID REFERENCES drivers(id) NOT NULL,
    vehicle_id      UUID REFERENCES vehicles(id) NOT NULL,
    source          VARCHAR(20) NOT NULL,  -- 'prima', 'manual'
    external_id     VARCHAR(100),

    started_at      TIMESTAMPTZ NOT NULL,
    ended_at        TIMESTAMPTZ,

    -- Métricas del turno
    km_free         DECIMAL(10,2),    -- km en libre
    km_occupied     DECIMAL(10,2),    -- km en ocupado
    max_speed       DECIMAL(5,1),     -- Velocidad máxima
    total_earnings  DECIMAL(10,2),    -- Total recaudado

    raw_data        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Evitar duplicados con external_id (solo cuando no es NULL)
CREATE UNIQUE INDEX idx_unique_shift_external_id
ON shifts (source, external_id)
WHERE external_id IS NOT NULL;
```

### 4.6 Tabla: `sync_logs` (Logs de Sincronización - Observability)

```sql
CREATE TABLE sync_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source              VARCHAR(20) NOT NULL,
    sync_type           VARCHAR(20) NOT NULL,  -- 'full', 'incremental'
    status              VARCHAR(20) NOT NULL,  -- 'started', 'completed', 'failed', 'retrying'

    -- Observability enhancements
    celery_task_id      UUID,                   -- ID de tarea Celery
    worker_hostname     VARCHAR(255),           -- Worker que ejecutó la tarea
    retry_count         INTEGER DEFAULT 0,      -- Número de reintentos

    records_found       INTEGER DEFAULT 0,
    records_created     INTEGER DEFAULT 0,
    records_updated     INTEGER DEFAULT 0,
    records_skipped     INTEGER DEFAULT 0,

    error_message       TEXT,
    error_details       JSONB,
    stack_trace         TEXT,

    started_at          TIMESTAMPTZ NOT NULL,
    completed_at        TIMESTAMPTZ,
    duration_seconds    DECIMAL(10,2)
);

-- Índices para monitoreo
CREATE INDEX idx_sync_logs_status ON sync_logs(status, started_at DESC);
CREATE INDEX idx_sync_logs_source ON sync_logs(source, started_at DESC);
CREATE INDEX idx_sync_logs_failed ON sync_logs(status) WHERE status = 'failed';
```

### 4.7 Tabla: `freenow_imports` (Control de Archivos Importados)

```sql
CREATE TABLE freenow_imports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename        VARCHAR(255) NOT NULL,
    file_hash       VARCHAR(64) NOT NULL,  -- SHA-256 del archivo
    file_size_bytes BIGINT,
    import_date     DATE NOT NULL,
    
    status          VARCHAR(20) NOT NULL,  -- 'pending', 'processing', 'completed', 'failed'
    records_imported INTEGER DEFAULT 0,
    error_message   TEXT,
    
    uploaded_at     TIMESTAMPTZ DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,
    
    UNIQUE(file_hash)  -- Evitar procesar el mismo archivo dos veces
);

CREATE INDEX idx_freenow_imports_status ON freenow_imports(status, import_date DESC);
```

### 4.8 Tabla: `daily_summaries` (Resúmenes Diarios - Materializada)

```sql
CREATE TABLE daily_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date            DATE NOT NULL,
    driver_id       UUID REFERENCES drivers(id),
    vehicle_id      UUID REFERENCES vehicles(id),

    -- Por fuente
    trips_uber      INTEGER DEFAULT 0,
    trips_freenow   INTEGER DEFAULT 0,
    trips_prima     INTEGER DEFAULT 0,
    trips_street    INTEGER DEFAULT 0,

    -- Totales
    total_trips     INTEGER DEFAULT 0,
    total_km        DECIMAL(10,2) DEFAULT 0,
    total_gross     DECIMAL(10,2) DEFAULT 0,
    total_commission DECIMAL(10,2) DEFAULT 0,
    total_net       DECIMAL(10,2) DEFAULT 0,

    -- Ratios
    avg_trip_value  DECIMAL(10,2),
    euro_per_km     DECIMAL(10,2),

    calculated_at   TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(date, driver_id, vehicle_id)
);
```

---

## 5. Seguridad

### 5.1 Gestión de Credenciales y Secretos

|| Aspecto | Estrategia |
||---------|-----------|
|| **Desarrollo Local** | `.env` files con `.env.example` en Git (sin valores reales) |
|| **Producción** | Secrets Manager (Doppler, Vault, o Docker Secrets) |
|| **API Keys** | Uber OAuth tokens, credenciales FreeNow/Prima |
|| **Base de Datos** | Passwords en variables de entorno, nunca hardcoded |

**Reglas Inquebrantables:**
- ❌ NUNCA commitear `.env` con valores reales
- ❌ NUNCA hardcodear credenciales en código
- ✅ Usar `.env.example` como plantilla
- ✅ Rotar API keys periódicamente
- ✅ Acceso mínimo necesario (least privilege)

### 5.2 OAuth y Gestión de Tokens (Uber)

**Lifecycle completo de OAuth 2.0 para Uber API:**

```
┌──────────────────────────────────────────────────────────────┐
│                    OAUTH 2.0 FLOW (UBER)                      │
├──────────────────────────────────────────────────────────────┤
│  1. Autorización Inicial                                      │
│     - Conductor visita URL de autorización                   │
│     - Login en Uber + acepta permisos                         │
│     - Redirect con authorization_code                         │
│                                                               │
│  2. Intercambio de Código                                     │
│     - POST /oauth/v2/token con authorization_code            │
│     - Recibe: access_token (expira en 30 días)               │
│               refresh_token (expira en 90 días)               │
│                                                               │
│  3. Almacenamiento Seguro                                     │
│     - Encrypt tokens con Fernet (symmetric encryption)        │
│     - Store en tabla `platform_tokens`                        │
│                                                               │
│  4. Uso y Renovación Automática                               │
│     - Antes de cada request, verificar expiración            │
│     - Si access_token expirado → refresh automático          │
│     - Si refresh_token expirado → notificar para re-auth     │
│                                                               │
│  5. Revocación                                                │
│     - Conductor puede revocar desde app Uber                  │
│     - Sistema detecta 401 → marca token como inválido        │
│     - Notifica al admin para re-autorización                  │
└──────────────────────────────────────────────────────────────┘
```

**Tabla para almacenar tokens:**

```sql
CREATE TABLE platform_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id       UUID REFERENCES drivers(id) NOT NULL,
    platform        VARCHAR(20) NOT NULL,  -- 'uber', 'freenow', etc.
    
    -- Tokens encriptados
    access_token_encrypted  TEXT NOT NULL,
    refresh_token_encrypted TEXT,
    
    -- Metadata
    token_type      VARCHAR(20) DEFAULT 'Bearer',
    expires_at      TIMESTAMPTZ NOT NULL,
    refresh_expires_at TIMESTAMPTZ,
    scopes          TEXT[],
    
    -- Estado
    is_valid        BOOLEAN DEFAULT TRUE,
    revoked_at      TIMESTAMPTZ,
    last_refreshed  TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(driver_id, platform)
);
```

**Rate Limiting & Backoff Strategy:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
async def fetch_uber_trips_with_backoff(access_token: str, date: str):
    """
    Fetch con exponential backoff para manejar rate limits.
    
    Si recibe 429 (Too Many Requests):
      - 1er intento: espera 4s
      - 2do intento: espera 8s
      - 3er intento: espera 16s
    """
    response = await uber_client.get(
        "/partners/trips",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"from_time": f"{date}T00:00:00Z", "to_time": f"{date}T23:59:59Z"}
    )
    
    if response.status_code == 429:
        # Log rate limit hit para métricas
        log_rate_limit_hit("uber", response.headers.get("X-Rate-Limit-Reset"))
        raise Exception("Rate limited")
    
    response.raise_for_status()
    return response.json()
```

### 5.3 Autenticación y Autorización del API

|| Endpoint Type | Estrategia |
||---------------|-----------|
|| **Dashboard (Frontend)** | JWT tokens con refresh mechanism |
|| **API Interna (Celery tasks)** | Internal API key |
|| **Webhooks (si aplica)** | HMAC signature validation |

**Implementación FastAPI:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica JWT token"""
    token = credentials.credentials
    # Validar token
    if not is_valid_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return decode_token(token)

# Uso en endpoints
@app.get("/api/trips", dependencies=[Depends(verify_token)])
async def get_trips():
    ...
```

**Niveles de Acceso:**
- **Admin** (Iván): Acceso completo, configuración, gestión de usuarios
- **Owner** (Elena): Acceso a sus propios vehículos y datos
- **Driver** (Asalariados): Solo lectura de sus propios datos

### 5.4 Protección de Datos Personales (GDPR/LOPD)

|| Tipo de Dato | Medida de Protección |
||--------------|---------------------|
|| **PII Drivers** | Encriptación en tránsito (TLS), encriptación en reposo (PostgreSQL) |
|| **Coordenadas GPS** | Solo almacenar si es necesario para análisis, anonimizar después de 90 días |
|| **Datos Financieros** | Auditoría de acceso, backups encriptados |

**Política de Retención Completa (GDPR/LOPD Compliance):**

|| Tipo de Dato | Retención | Acción Automática | Justificación Legal |
||--------------|-----------|-------------------|---------------------|
|| **Coordenadas GPS** | 90 días | Anonimización | Análisis operativo temporal |
|| **Datos Financieros** | 7 años | Archivo (no borrado) | Obligación fiscal (Ley General Tributaria) |
|| **Nombres/Teléfonos Conductores** | Mientras activo + 1 año | Anonimización | Gestión laboral/contractual |
|| **OAuth Tokens** | Mientras válido + 30 días | Purga + re-encrypt | Minimización de datos |
|| **Matrículas Vehículos** | 7 años | Archivo | Trazabilidad fiscal |
|| **Logs de Sincronización** | 1 año | Purga | Debugging y auditoría |

**Funciones de Anonimización/Purga:**

```sql
-- 1. Anonimización GPS (mantiene trips para fiscal, pero sin ubicación)
CREATE OR REPLACE FUNCTION anonymize_old_gps_data()
RETURNS void AS $$
BEGIN
    UPDATE trips
    SET origin_lat = NULL,
        origin_lng = NULL,
        dest_lat = NULL,
        dest_lng = NULL,
        origin_address = 'ANONYMIZED',
        dest_address = 'ANONYMIZED'
    WHERE started_at < NOW() - INTERVAL '90 days'
      AND origin_lat IS NOT NULL;
    
    RAISE NOTICE 'GPS data anonymized for trips older than 90 days';
END;
$$ LANGUAGE plpgsql;


-- 2. Anonimización conductores inactivos
CREATE OR REPLACE FUNCTION anonymize_inactive_drivers()
RETURNS void AS $$
BEGIN
    UPDATE drivers
    SET name = 'ANONYMIZED_' || id::text,
        email = NULL,
        phone = NULL,
        uber_driver_id = NULL,
        freenow_driver_id = NULL
    WHERE is_active = FALSE
      AND updated_at < NOW() - INTERVAL '1 year';
    
    RAISE NOTICE 'PII anonymized for inactive drivers (>1 year)';
END;
$$ LANGUAGE plpgsql;


-- 3. Purga de tokens expirados
CREATE OR REPLACE FUNCTION purge_expired_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM platform_tokens
    WHERE (expires_at < NOW() - INTERVAL '30 days')
       OR (is_valid = FALSE AND revoked_at < NOW() - INTERVAL '30 days');
    
    RAISE NOTICE 'Expired OAuth tokens purged';
END;
$$ LANGUAGE plpgsql;


-- 4. Purga de logs antiguos
CREATE OR REPLACE FUNCTION purge_old_sync_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM sync_logs
    WHERE started_at < NOW() - INTERVAL '1 year';
    
    RAISE NOTICE 'Sync logs older than 1 year purged';
END;
$$ LANGUAGE plpgsql;
```

**Workflow de Data Subject Requests (DSR):**

```python
# Tabla para tracking de DSRs
CREATE TABLE dsr_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_type    VARCHAR(20) NOT NULL,  -- 'access', 'erasure', 'portability', 'rectification'
    subject_type    VARCHAR(20) NOT NULL,  -- 'driver', 'owner'
    subject_id      UUID NOT NULL,
    
    requester_email VARCHAR(255) NOT NULL,
    verification_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'verified', 'rejected'
    
    status          VARCHAR(20) DEFAULT 'received',  -- 'received', 'processing', 'completed', 'rejected'
    completed_at    TIMESTAMPTZ,
    response_data   JSONB,  -- Para export requests
    
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);


# Implementación DSR
async def handle_dsr_access_request(driver_id: UUID) -> dict:
    """
    GDPR Article 15: Right of Access
    Exporta todos los datos personales del conductor
    """
    driver = db.query(Driver).get(driver_id)
    trips = db.query(Trip).filter(Trip.driver_id == driver_id).all()
    tokens = db.query(PlatformToken).filter(PlatformToken.driver_id == driver_id).all()
    
    export_data = {
        "personal_info": {
            "name": driver.name,
            "email": driver.email,
            "phone": driver.phone,
            "license_number": driver.license_number
        },
        "trips": [serialize_trip(t) for t in trips],
        "platform_integrations": [{"platform": t.platform, "connected_at": t.created_at} for t in tokens],
        "export_date": datetime.now(UTC).isoformat()
    }
    
    return export_data


async def handle_dsr_erasure_request(driver_id: UUID) -> None:
    """
    GDPR Article 17: Right to Erasure (Right to be Forgotten)
    
    IMPORTANTE: No podemos borrar datos fiscales (obligación legal 7 años).
    Anonimizamos PII pero mantenemos datos financieros agregados.
    """
    driver = db.query(Driver).get(driver_id)
    
    # 1. Verificar si hay obligación legal de retención
    if has_active_fiscal_obligations(driver):
        raise ValueError("Cannot fully erase: fiscal retention required. Only PII will be anonymized.")
    
    # 2. Anonimizar PII
    driver.name = f"ERASED_{driver.id}"
    driver.email = None
    driver.phone = None
    driver.license_number = f"ERASED_{driver.id}"
    
    # 3. Borrar tokens OAuth
    db.query(PlatformToken).filter(PlatformToken.driver_id == driver_id).delete()
    
    # 4. Mantener trips pero disociar del conductor (anonimizar)
    # NO borramos trips porque son necesarios para impuestos
    
    # 5. Log de erasure para auditoría
    log_dsr_action("erasure", driver_id, "PII anonymized, financial data retained for legal compliance")
    
    db.commit()
```

### 5.5 Seguridad de la Infraestructura

|| Componente | Medida |
||------------|--------|
|| **PostgreSQL** | Red interna Docker, no exponer puerto 5432 públicamente |
|| **FastAPI** | Rate limiting, CORS configurado, validación de inputs |
|| **Redis** | Red interna, requirepass configurado |
|| **Docker** | Non-root users, imágenes oficiales, escaneo de vulnerabilidades |

**Configuración docker-compose.yml:**
```yaml
services:
  db:
    image: postgres:15-alpine
    networks:
      - internal
    # NO publicar puerto externamente en producción
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
  
  api:
    build: ./src
    ports:
      - "8000:8000"  # Solo API expuesto
    networks:
      - internal
      - public
    depends_on:
      - db
      - redis

networks:
  internal:
    driver: bridge
  public:
    driver: bridge
```

### 5.6 Validación de Inputs (Prevención SQL Injection)

**SIEMPRE usar ORM (SQLAlchemy) con parámetros:**
```python
# ✅ CORRECTO - Parámetros seguros
def get_trips_by_driver(driver_id: UUID) -> list[Trip]:
    return db.query(Trip).filter(Trip.driver_id == driver_id).all()

# ❌ INCORRECTO - Vulnerable a SQL injection
def get_trips_unsafe(driver_name: str):
    query = f"SELECT * FROM trips WHERE driver_name = '{driver_name}'"
    return db.execute(query)
```

**Validación Pydantic:**
```python
from pydantic import BaseModel, EmailStr, constr
from uuid import UUID

class DriverCreate(BaseModel):
    name: constr(min_length=1, max_length=100)
    email: EmailStr
    phone: constr(regex=r'^\+?[1-9]\d{1,14}$')  # E.164 format
    license_number: constr(min_length=5, max_length=50)
```

---

## 6. Flujo de Sincronización Diaria

### 6.1 Programación

```
┌───────────────────────────────────────────────────────────────────┐
│                    CRON SCHEDULE (Celery)                          │
├───────────────────────────────────────────────────────────────────┤
│                          TAREAS DIARIAS                            │
│  02:00 AM   │  sync_uber_task         │  Sync últimas 24h         │
│  02:05 AM   │  sync_prima_task        │  Sync turnos y viajes     │
│  02:10 AM   │  sync_freenow_task      │  Procesar CSV nuevo       │
│  02:20 AM   │  deduplicate_trips_task │  Fusionar duplicados      │
│  02:30 AM   │  assign_shifts_task     │  Asignar trips a turnos   │
│  03:00 AM   │  calculate_summaries    │  Regenerar resúmenes      │
│  03:30 AM   │  send_daily_report      │  Email/Telegram           │
├───────────────────────────────────────────────────────────────────┤
│                     TAREAS DE MANTENIMIENTO                        │
│  SUNDAY     │  anonymize_gps_task     │  Anonimizar GPS > 90 días │
│  04:00 AM   │                         │  (GDPR/LOPD compliance)   │
└───────────────────────────────────────────────────────────────────┘
```

### 6.2 Flujo Detallado con Manejo de Errores

```python
# Implementación con Celery Chord para paralelización resiliente

from celery import group, chord

@celery.app.task(bind=True, max_retries=3)
def sync_uber_task(self, date: str):
    """Sincronización Uber con reintentos"""
    try:
        uber_trips = uber_connector.fetch_trips(
            from_time=f"{date}T00:00:00Z",
            to_time=f"{date}T23:59:59Z"
        )
        saved_count = save_trips(uber_trips, source='uber')
        log_sync_success('uber', saved_count)
        return {'source': 'uber', 'status': 'success', 'count': saved_count}
    
    except Exception as exc:
        log_sync_error('uber', str(exc))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        return {'source': 'uber', 'status': 'failed', 'error': str(exc)}


@celery.app.task
def sync_prima_task(date: str):
    """Sincronización Prima"""
    try:
        prima_data = prima_connector.fetch_shifts_and_trips(date=date)
        save_shifts(prima_data.shifts)
        saved_count = save_trips(prima_data.trips, source='prima')
        log_sync_success('prima', saved_count)
        return {'source': 'prima', 'status': 'success', 'count': saved_count}
    except Exception as exc:
        log_sync_error('prima', str(exc))
        return {'source': 'prima', 'status': 'failed', 'error': str(exc)}


@celery.app.task
def sync_freenow_task(date: str):
    """
    Sincronización FreeNow (semi-manual con validación y gap detection).
    """
    try:
        csv_path = f"imports/freenow_{date}.csv"
        
        # 1. Verificar existencia del archivo
        if not os.path.exists(csv_path):
            # Detectar gap: si han pasado más de X días, alertar
            last_successful_import = get_last_successful_freenow_import()
            days_since_last = (datetime.now() - last_successful_import).days
            
            if days_since_last > 3:  # Más de 3 días sin importar
                asyncio.run(send_telegram_alert(
                    "warning",
                    f"⚠️ FreeNow CSV missing for {days_since_last} days!\n"
                    f"Last import: {last_successful_import.strftime('%Y-%m-%d')}\n"
                    f"Missing date: {date}"
                ))
            
            log_sync_skipped('freenow', f'CSV no disponible (gap: {days_since_last} días)')
            return {'source': 'freenow', 'status': 'skipped', 'gap_days': days_since_last}
        
        # 2. Validar que no sea un archivo ya procesado (por hash)
        file_hash = calculate_file_hash(csv_path)
        existing_import = db.query(FreeNowImport).filter_by(file_hash=file_hash).first()
        
        if existing_import:
            log_sync_skipped('freenow', 'Archivo ya procesado anteriormente')
            return {'source': 'freenow', 'status': 'duplicate', 'original_import': existing_import.id}
        
        # 3. Validar schema del CSV antes de procesar
        try:
            validate_freenow_csv_schema(csv_path)
        except SchemaValidationError as e:
            # Schema cambió → notificar para actualizar parser
            asyncio.run(send_telegram_alert(
                "critical",
                f"🚨 FreeNow CSV schema changed!\n"
                f"File: {csv_path}\n"
                f"Error: {str(e)}\n"
                f"Parser needs update!"
            ))
            raise
        
        # 4. Procesar archivo
        file_size = os.path.getsize(csv_path)
        import_record = FreeNowImport(
            filename=os.path.basename(csv_path),
            file_hash=file_hash,
            file_size_bytes=file_size,
            import_date=datetime.strptime(date, '%Y-%m-%d').date(),
            status='processing'
        )
        db.add(import_record)
        db.commit()
        
        freenow_trips = freenow_connector.parse_csv(csv_path)
        saved_count = save_trips(freenow_trips, source='freenow')
        
        # 5. Actualizar registro de importación
        import_record.status = 'completed'
        import_record.records_imported = saved_count
        import_record.processed_at = datetime.now(UTC)
        db.commit()
        
        log_sync_success('freenow', saved_count)
        return {'source': 'freenow', 'status': 'success', 'count': saved_count}
        
    except SchemaValidationError as exc:
        if 'import_record' in locals():
            import_record.status = 'failed'
            import_record.error_message = f"Schema validation failed: {str(exc)}"
            db.commit()
        
        log_sync_error('freenow', f"Schema validation failed: {str(exc)}")
        return {'source': 'freenow', 'status': 'failed', 'error': 'schema_validation'}
        
    except Exception as exc:
        if 'import_record' in locals():
            import_record.status = 'failed'
            import_record.error_message = str(exc)
            db.commit()
        
        log_sync_error('freenow', str(exc))
        return {'source': 'freenow', 'status': 'failed', 'error': str(exc)}


def validate_freenow_csv_schema(csv_path: str):
    """
    Valida que el CSV de FreeNow tenga el schema esperado.
    Raises SchemaValidationError si falla.
    """
    import pandas as pd
    
    EXPECTED_COLUMNS = {
        'trip_id', 'date', 'time', 'pickup_address', 'dropoff_address',
        'distance_km', 'duration_minutes', 'gross_amount', 'commission', 'net_amount'
    }
    
    try:
        df = pd.read_csv(csv_path, nrows=1)
        actual_columns = set(df.columns)
        
        missing_columns = EXPECTED_COLUMNS - actual_columns
        if missing_columns:
            raise SchemaValidationError(f"Missing columns: {missing_columns}")
        
        # Validar tipos de datos esperados
        # ... más validaciones según sea necesario
        
    except Exception as e:
        raise SchemaValidationError(f"CSV validation failed: {str(e)}")


def calculate_file_hash(filepath: str) -> str:
    """Calcula SHA-256 hash del archivo"""
    import hashlib
    
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    
    return sha256.hexdigest()


class SchemaValidationError(Exception):
    """Custom exception para errores de validación de schema"""
    pass


@celery.app.task
def deduplicate_trips_task(date: str):
    """Detecta y fusiona trips duplicados entre fuentes"""
    # Encuentra trips del mismo vehículo con timestamps cercanos
    duplicates = detect_duplicate_trips(date)
    
    for group in duplicates:
        # Prima es la fuente canónica (datos más completos)
        canonical = next((t for t in group if t.source == 'prima'), group[0])
        
        for trip in group:
            if trip.id != canonical.id:
                trip.merged_into_trip_id = canonical.id
                trip.is_canonical = False
        
        db.commit()
    
    return {'deduplicated': len(duplicates)}


@celery.app.task
def assign_shifts_to_trips_task(date: str):
    """Asigna shift_id a todos los trips (incluidos Uber/FreeNow)"""
    # Para cada shift de Prima del día
    shifts = db.query(Shift).filter(
        Shift.started_at >= f"{date}T00:00:00",
        Shift.started_at < f"{date}T23:59:59"
    ).all()
    
    for shift in shifts:
        # Encuentra trips en ese rango temporal
        trips = db.query(Trip).filter(
            Trip.vehicle_id == shift.vehicle_id,
            Trip.started_at >= shift.started_at,
            Trip.started_at <= shift.ended_at,
            Trip.shift_id.is_(None)
        ).all()
        
        for trip in trips:
            trip.shift_id = shift.id
    
    db.commit()


@celery.app.task
def send_final_report(summary_result, date: str, sync_results: list):
    """Envía reporte final con todos los resultados"""
    send_telegram_summary(date, sync_results)
    return {"status": "completed", "date": date}


# Orquestación principal con Celery Chain (evita .apply().get() que bloquea workers)
def trigger_daily_sync(date: str):
    """
    Ejecuta todas las sincronizaciones en paralelo,
    luego ejecuta post-procesamiento en cadena secuencial.
    """
    from celery import chain, chord
    
    # Fase 1: Sync en paralelo (group)
    sync_tasks = group(
        sync_uber_task.s(date),
        sync_prima_task.s(date),
        sync_freenow_task.s(date)
    )
    
    # Fase 2: Post-procesamiento secuencial (chain)
    # IMPORTANTE: Usar chain() en lugar de .apply().get() evita bloquear el worker
    post_process_pipeline = chain(
        deduplicate_trips_task.s(date),           # 1. Deduplicar
        assign_shifts_to_trips_task.s(date),      # 2. Asignar shifts
        calculate_summaries_task.s(date),         # 3. Calcular resúmenes
        send_final_report.s(date, sync_results=[])  # 4. Enviar reporte
    )
    
    # Chord: group ejecuta en paralelo, luego callback inicia la chain
    workflow = chord(sync_tasks)(post_process_pipeline)
    
    return workflow
```

### 6.3 Deduplicación entre Fuentes

**Problema:** Un mismo viaje puede aparecer en Prima (taxímetro) y FreeNow/Uber (plataforma).

**Solución:** Deduplicación temporal-espacial basada en heurísticas configurables + workflow de revisión manual.

#### 6.3.1 Configuración de Heurísticas

```python
# Config centralizada (settings.py o DB)
DEDUP_CONFIG = {
    "time_window_seconds": 120,        # 2 minutos (configurable)
    "amount_tolerance_pct": 0.10,      # ±10% (configurable)
    "require_manual_review_above_pct": 0.20,  # >20% diferencia → revisión manual
    "canonical_source_priority": ["prima", "uber", "freenow", "street"]
}
```

#### 6.3.2 Tabla de Revisión Manual

```sql
CREATE TABLE dedup_manual_reviews (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id_1       UUID REFERENCES trips(id) NOT NULL,
    trip_id_2       UUID REFERENCES trips(id) NOT NULL,
    
    -- Metadata de la detección
    time_diff_seconds INTEGER,
    amount_diff_pct   DECIMAL(5,2),
    confidence_score  DECIMAL(3,2),  -- 0.0 - 1.0
    
    -- Decisión
    status          VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'needs_info'
    is_duplicate    BOOLEAN,
    canonical_trip_id UUID REFERENCES trips(id),
    reviewed_by     UUID REFERENCES drivers(id),
    reviewed_at     TIMESTAMPTZ,
    notes           TEXT,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_dedup_reviews_pending ON dedup_manual_reviews(status) WHERE status = 'pending';
```

#### 6.3.3 Lógica de Deduplicación con Governance

```python
def detect_duplicate_trips(date: str, config: dict = DEDUP_CONFIG) -> dict:
    """
    Detecta trips duplicados con heurísticas configurables.
    Returns: {auto_merged: [...], needs_review: [...]}
    """
    all_trips = db.query(Trip).filter(
        Trip.started_at >= f"{date}T00:00:00",
        Trip.is_canonical == True
    ).order_by(Trip.vehicle_id, Trip.started_at).all()
    
    auto_merged = []
    needs_review = []
    
    for i, trip1 in enumerate(all_trips):
        group = [trip1]
        
        for trip2 in all_trips[i+1:]:
            if trip1.vehicle_id != trip2.vehicle_id:
                continue
            
            time_diff = abs((trip2.started_at - trip1.started_at).total_seconds())
            if time_diff > config["time_window_seconds"]:
                break
            
            amount_diff_pct = abs(trip1.gross_amount - trip2.gross_amount) / max(trip1.gross_amount, 0.01)
            
            if amount_diff_pct < config["amount_tolerance_pct"]:
                # Alta confianza → auto-merge
                group.append(trip2)
                confidence = 1.0 - amount_diff_pct
                
            elif amount_diff_pct < config["require_manual_review_above_pct"]:
                # Confianza media → marcar para revisión manual
                needs_review.append({
                    "trip1": trip1,
                    "trip2": trip2,
                    "time_diff": time_diff,
                    "amount_diff_pct": amount_diff_pct,
                    "confidence": 0.5
                })
        
        if len(group) > 1:
            auto_merged.append(group)
    
    # Guardar casos de revisión manual
    for review_case in needs_review:
        create_manual_review(review_case)
    
    return {"auto_merged": auto_merged, "needs_review": needs_review}


def merge_trip_group(trips: list[Trip], canonical_source_priority: list[str]):
    """
    Fusiona grupo de trips duplicados eligiendo el canónico.
    Prioridad: Prima > Uber > FreeNow > Street
    """
    # Ordenar por prioridad de fuente
    sorted_trips = sorted(trips, key=lambda t: canonical_source_priority.index(t.source))
    
    canonical = sorted_trips[0]
    canonical.is_canonical = True
    
    for trip in sorted_trips[1:]:
        trip.is_canonical = False
        trip.merged_into_trip_id = canonical.id
        
        # Enrich canonical con datos que falten (ejemplo: tips de Uber)
        if trip.tips > 0 and canonical.tips == 0:
            canonical.tips = trip.tips
            canonical.amount_breakdown = {
                **canonical.amount_breakdown,
                "tips_source": trip.source
            }
    
    db.commit()
    log_dedup_action(canonical, sorted_trips[1:])
```

**Workflow de Revisión Manual:**
1. Sistema detecta duplicados ambiguos (>10% pero <20% diferencia)
2. Crea registro en `dedup_manual_reviews` con status='pending'
3. Dashboard muestra lista de casos pendientes con comparativa lado a lado
4. Admin revisa y decide: "Es duplicado" o "Son viajes diferentes"
5. Sistema aplica decisión y aprende (opcional: ML futuro)

**Estrategia de Fusión:**
1. **Prioridad de fuentes**: Prima > Uber > FreeNow > Street (configurable)
2. **Enriquecimiento**: Si trip secundario tiene datos que faltan en canónico, se copian
3. **Trazabilidad**: Todo merge se logea con metadata de decisión

```sql
-- Consulta para obtener solo trips únicos (sin duplicados)
SELECT * FROM trips
WHERE is_canonical = TRUE;

-- Obtener casos que requieren revisión manual
SELECT 
    dr.*,
    t1.source as source_1,
    t1.gross_amount as amount_1,
    t2.source as source_2,
    t2.gross_amount as amount_2
FROM dedup_manual_reviews dr
JOIN trips t1 ON dr.trip_id_1 = t1.id
JOIN trips t2 ON dr.trip_id_2 = t2.id
WHERE dr.status = 'pending'
ORDER BY dr.created_at DESC;
```

### 6.4 Deduplicación por `external_id`

El índice único parcial evita duplicados cuando existe `external_id`:

```sql
-- Si intentas insertar el mismo external_id dos veces
INSERT INTO trips (source, external_id, ...)
VALUES ('uber', 'trip_abc123', ...)
ON CONFLICT ON CONSTRAINT idx_unique_trip_external_id
DO UPDATE SET
    updated_at = NOW(),
    raw_data = EXCLUDED.raw_data
WHERE trips.raw_data IS DISTINCT FROM EXCLUDED.raw_data;
```

---

## 6.7 Observability y Alerting

### 6.7.1 Métricas Prometheus

```python
from prometheus_client import Counter, Histogram, Gauge

# Métricas de sincronización
sync_tasks_total = Counter(
    'taxi_api_sync_tasks_total',
    'Total sync tasks executed',
    ['source', 'status']  # labels: uber/freenow/prima, success/failed
)

sync_duration_seconds = Histogram(
    'taxi_api_sync_duration_seconds',
    'Sync task duration',
    ['source'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

sync_records_processed = Counter(
    'taxi_api_sync_records_total',
    'Records processed during sync',
    ['source', 'action']  # action: created/updated/skipped
)

# Métricas de deduplicación
dedup_matches_found = Counter(
    'taxi_api_dedup_matches_total',
    'Duplicate trips detected',
    ['auto_merged', 'needs_review']
)

# Métricas de API
api_requests_total = Counter(
    'taxi_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration_seconds = Histogram(
    'taxi_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

# Métricas de negocio
active_drivers_gauge = Gauge(
    'taxi_api_active_drivers',
    'Number of active drivers'
)

daily_trips_gauge = Gauge(
    'taxi_api_daily_trips',
    'Trips completed today',
    ['source']
)
```

### 6.7.2 Alertas (Prometheus Alertmanager)

```yaml
# prometheus_alerts.yml
groups:
  - name: taxi_api_sync
    interval: 5m
    rules:
      # Alerta crítica: Sync fallando consistentemente
      - alert: SyncFailureRate
        expr: rate(taxi_api_sync_tasks_total{status="failed"}[1h]) > 0.05
        for: 10m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "Sync failure rate > 5% for {{ $labels.source }}"
          description: "{{ $labels.source }} sync has been failing frequently"
          
      # Alerta warning: Sync tardando mucho
      - alert: SyncDurationHigh
        expr: histogram_quantile(0.95, taxi_api_sync_duration_seconds_bucket) > 120
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Sync duration p95 > 2 minutes"
          
      # Alerta crítica: No se ha ejecutado sync en 2 horas
      - alert: SyncNotRunning
        expr: time() - max(taxi_api_sync_tasks_total) > 7200
        labels:
          severity: critical
        annotations:
          summary: "No sync tasks executed in last 2 hours"
          description: "Celery scheduler may be down"
          
      # Alerta info: Muchos duplicados necesitan revisión manual
      - alert: HighDedupReviewQueue
        expr: count(dedup_manual_reviews{status="pending"}) > 50
        labels:
          severity: info
        annotations:
          summary: "{{ $value }} trips need manual dedup review"

  - name: taxi_api_business
    interval: 1h
    rules:
      # Alerta business: Caída significativa en viajes diarios
      - alert: DailyTripsDropped
        expr: daily_trips_gauge < daily_trips_gauge offset 7d * 0.7
        for: 3h
        labels:
          severity: warning
        annotations:
          summary: "Daily trips 30% below last week average"
```

### 6.7.3 Integración con Telegram/Email

```python
import aiohttp

async def send_telegram_alert(alert_level: str, message: str):
    """Envía alerta a canal Telegram"""
    telegram_bot_token = settings.TELEGRAM_BOT_TOKEN
    telegram_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    
    emoji = {
        "critical": "🚨",
        "warning": "⚠️",
        "info": "ℹ️"
    }.get(alert_level, "📢")
    
    formatted_message = f"{emoji} *{alert_level.upper()}*\n\n{message}"
    
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
            json={
                "chat_id": telegram_chat_id,
                "text": formatted_message,
                "parse_mode": "Markdown"
            }
        )


# Ejemplo de uso en sync tasks
@celery.app.task(bind=True, max_retries=3)
def sync_uber_task(self, date: str):
    try:
        # ... sync logic ...
        sync_tasks_total.labels(source='uber', status='success').inc()
        
    except Exception as exc:
        sync_tasks_total.labels(source='uber', status='failed').inc()
        
        if self.request.retries >= self.max_retries:
            # Última retry falló → alerta crítica
            asyncio.run(send_telegram_alert(
                "critical",
                f"Uber sync failed after {self.max_retries} retries:\n{str(exc)}"
            ))
        
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
```

### 6.7.4 Dashboard Grafana

```json
{
  "dashboard": {
    "title": "TAXI API - Sync Monitoring",
    "panels": [
      {
        "title": "Sync Success Rate (24h)",
        "targets": [
          {
            "expr": "rate(taxi_api_sync_tasks_total{status=\"success\"}[24h]) / rate(taxi_api_sync_tasks_total[24h])"
          }
        ]
      },
      {
        "title": "Sync Duration p95",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, taxi_api_sync_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Records Processed (Today)",
        "targets": [
          {
            "expr": "sum(increase(taxi_api_sync_records_total[24h])) by (source)"
          }
        ]
      },
      {
        "title": "Pending Manual Reviews",
        "targets": [
          {
            "expr": "count(dedup_manual_reviews{status=\"pending\"})"
          }
        ]
      }
    ]
  }
}
```

### 6.7.5 SLOs (Service Level Objectives)

|| Métrica | Objetivo | Medición |
||---------|----------|----------|
|| **Sync Uptime** | 99.5% | % de syncs exitosos en ventana de 30 días |
|| **Sync Latency** | p95 < 2 min | Tiempo de ejecución percentil 95 |
|| **Data Freshness** | < 24h | Tiempo desde último sync exitoso |
|| **API Availability** | 99.9% | Uptime del API FastAPI |
|| **API Latency** | p95 < 500ms | Tiempo de respuesta endpoints lectura |

---

## 7. API Contract - Endpoints FastAPI

### 7.1 Principios de Diseño

|| Principio | Implementación |
||-----------|----------------|
|| **Estilo** | REST con recursos orientados a colecciones |
|| **Versionado** | `/api/v1/...` en la URL |
|| **Autenticación** | JWT Bearer token en header `Authorization` |
|| **Paginación** | Cursor-based + limit (mejor que offset para tablas grandes) |
|| **Filtrado** | Query parameters estándar |
|| **Rate Limiting** | 100 req/min por cliente (configurable) |

### 7.2 Endpoints Principales

**Trips (Viajes)**

```python
GET    /api/v1/trips
       Query params: 
         - driver_id: UUID (opcional)
         - vehicle_id: UUID (opcional)
         - source: str (uber|freenow|prima|street, opcional)
         - canonical_only: bool (default: true, solo trips no duplicados)
         - start_date: date
         - end_date: date
         - limit: int (default: 50, max: 500)
         - cursor: str (para paginación)
       
       Response:
         {
           "data": [Trip],
           "pagination": {
             "next_cursor": str | null,
             "has_more": bool,
             "total_count": int (aproximado)
           }
         }

GET    /api/v1/trips/{trip_id}
POST   /api/v1/trips             # Manual entry (street trips)
PATCH  /api/v1/trips/{trip_id}   # Corrections
```

**Drivers (Conductores)**

```python
GET    /api/v1/drivers
GET    /api/v1/drivers/{driver_id}
GET    /api/v1/drivers/{driver_id}/stats  # Métricas agregadas
POST   /api/v1/drivers
PATCH  /api/v1/drivers/{driver_id}
```

**Summaries (Resúmenes)**

```python
GET    /api/v1/summaries/daily
       Query params:
         - start_date: date
         - end_date: date
         - driver_id: UUID (opcional)
         - vehicle_id: UUID (opcional)

GET    /api/v1/summaries/monthly
GET    /api/v1/summaries/comparative  # Comparativas entre períodos
```

**Sync (Sincronización)**

```python
POST   /api/v1/sync/trigger/{source}  # Manual sync trigger
GET    /api/v1/sync/logs              # Historial de sincronizaciones
GET    /api/v1/sync/status            # Estado actual de sincronizaciones
```

### 7.3 Modelo de Respuesta

**Éxito:**
```json
{
  "data": { ... },
  "metadata": {
    "timestamp": "2026-01-27T10:00:00Z",
    "version": "1.0"
  }
}
```

**Error:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date range",
    "details": {
      "field": "start_date",
      "issue": "Must be before end_date"
    }
  },
  "request_id": "uuid"
}
```

### 7.4 Control de Acceso (RBAC)

|| Rol | Permisos |
||------|----------|
|| **Admin** (Iván) | Todos los endpoints, todos los recursos |
|| **Owner** (Elena) | Solo sus vehículos y conductores |
|| **Driver** (Asalariados) | Solo lectura de sus propios datos |

### 7.5 Rate Limiting

- **Por IP**: 100 req/min para endpoints de lectura
- **Por API Key**: 500 req/min para integraciones
- **Sync endpoints**: 10 req/hora (evitar abuse)

### 7.6 Timezone Handling

**Regla crítica:** Todos los timestamps se almacenan en **UTC** (`TIMESTAMPTZ`).

```python
# Ingestion de datos
def normalize_timestamp(source_timestamp: str, source_timezone: str = 'Europe/Madrid') -> datetime:
    """
    Convierte timestamp de fuente externa a UTC.
    
    Args:
        source_timestamp: Timestamp en formato local
        source_timezone: Timezone de la fuente (default: Europe/Madrid)
    
    Returns:
        datetime en UTC
    """
    local_dt = parser.parse(source_timestamp)
    if local_dt.tzinfo is None:
        # Asume timezone de la fuente si no viene especificado
        tz = pytz.timezone(source_timezone)
        local_dt = tz.localize(local_dt)
    
    return local_dt.astimezone(pytz.UTC)
```

**API responses:** El cliente especifica timezone preferido en header `X-Timezone` o se asume UTC.

---

## 8. Dashboard - Métricas Clave

### 8.1 Vista General (Home)

| Métrica | Descripción |
|---------|-------------|
| **Ingresos Hoy/Semana/Mes/Año** | Bruto, comisiones, neto |
| **Viajes por Período** | Contador con comparativa |
| **KM Recorridos** | Total, libre vs ocupado |
| **Por Conductor** | Desglose Iván vs Elena |

### 8.2 Análisis de Rentabilidad

```
┌─────────────────────────────────────────────────────────┐
│  €/km por Plataforma          €/hora por Franja Horaria │
│  ┌─────────────────┐          ┌─────────────────────┐   │
│  │ Uber    │ 1.85€ │          │ 06-10h │ 18.5€/h   │   │
│  │ FreeNow │ 1.72€ │          │ 10-14h │ 15.2€/h   │   │
│  │ Calle   │ 1.90€ │          │ 14-18h │ 16.8€/h   │   │
│  │ Prima   │ 1.78€ │          │ 18-22h │ 22.1€/h   │   │
│  └─────────────────┘          │ 22-06h │ 19.4€/h   │   │
│                               └─────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Mapa de Calor

- Zonas más rentables
- Orígenes/destinos frecuentes
- Heatmap por hora del día

### 8.4 Reporting Fiscal

| Reporte | Formato | Frecuencia |
|---------|---------|------------|
| Resumen mensual | Excel/CSV | Mensual |
| Desglose IVA | PDF | Trimestral |
| Libro de servicios | CSV | Bajo demanda |
| Facturas plataformas | PDF links | Mensual |

---

## 9. Estructura del Proyecto

```
taxi-api/
├── README.md
├── TAXI_API_SPEC.md          # Este documento
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── main.py               # FastAPI app
│   ├── config.py             # Settings con pydantic
│   │
│   ├── domain/               # Entidades de dominio
│   │   ├── driver.py
│   │   ├── vehicle.py
│   │   ├── trip.py
│   │   └── shift.py
│   │
│   ├── application/          # Casos de uso
│   │   ├── sync_uber.py
│   │   ├── sync_freenow.py
│   │   ├── sync_prima.py
│   │   └── calculate_summaries.py
│   │
│   ├── infrastructure/       # Implementaciones
│   │   ├── database/
│   │   │   ├── models.py     # SQLAlchemy models
│   │   │   └── repositories/
│   │   │
│   │   ├── connectors/
│   │   │   ├── uber_connector.py
│   │   │   ├── freenow_connector.py
│   │   │   └── prima_connector.py
│   │   │
│   │   └── external/
│   │       └── telegram.py
│   │
│   └── api/                  # Endpoints FastAPI
│       ├── routes/
│       │   ├── trips.py
│       │   ├── drivers.py
│       │   ├── reports.py
│       │   └── sync.py
│       └── schemas/
│
├── tasks/                    # Celery tasks
│   ├── __init__.py
│   └── sync_tasks.py
│
├── migrations/               # Alembic
│   └── versions/
│
├── tests/                    # Tests TDD
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── frontend/                 # React Dashboard
│   ├── src/
│   └── package.json
│
└── scripts/
    ├── init_db.py
    └── import_csv.py
```

---

## 10. Estrategia de Testing

### 10.1 Niveles de Testing

|| Tipo | Herramienta | Cobertura Objetivo |
||------|-------------|-------------------|
|| **Unit Tests** | pytest | > 80% |
|| **Integration Tests** | pytest + testcontainers | Conectores, DB |
|| **E2E Tests** | pytest + requests | API endpoints |
|| **Contract Tests** | pact | CSV parsers |
|| **Property-Based** | hypothesis | Deduplication logic |

### 10.2 Tests Críticos

**Conectores (Mocks de APIs externas):**
```python
def test_uber_connector_rate_limit_handling():
    """Verifica que el conector maneja correctamente rate limits"""
    # Mock respuesta 429 Too Many Requests
    # Verificar exponential backoff
    pass

def test_prima_csv_parser_malformed_data():
    """Parser debe manejar CSVs con formato incorrecto"""
    pass
```

**Deduplicación (Property-based con Hypothesis):**
```python
@given(trips_data=st.lists(st.builds(Trip), min_size=2, max_size=100))
def test_deduplication_idempotency(trips_data):
    """La deduplicación debe ser idempotente"""
    result1 = deduplicate_trips(trips_data)
    result2 = deduplicate_trips(result1)
    assert result1 == result2
```

**API Endpoints:**
```python
def test_trips_endpoint_pagination():
    """Paginación debe ser consistente y no perder registros"""
    pass

def test_unauthorized_access_returns_401():
    """Sin JWT válido, debe retornar 401"""
    pass
```

---

## 11. Próximos Pasos

### 🔴 Prioridad ALTA (Esta semana)

| # | Tarea | Responsable | Estado |
|---|-------|-------------|--------|
| 1 | **CRÍTICO:** Verificar automatización real de Prima (exportación programada o API) | Iván | ⬜ Pendiente |
| 2 | **CRÍTICO:** Verificar automatización FreeNow (contactar soporte empresarial) | Iván | ⬜ Pendiente |
| 3 | Acceder a Prima cloud y exportar CSV de prueba manual | Iván | ⬜ Pendiente |
| 4 | Acceder a [portal.free-now.com](https://portal.free-now.com/) y descargar CSV | Iván/Elena | ⬜ Pendiente |
| 5 | Registrar app en [developer.uber.com](https://developer.uber.com) y verificar rate limits/data retention | Iván | ⬜ Pendiente |

### 🟡 Prioridad MEDIA (Próximas 2 semanas)

| # | Tarea | Notas |
|---|-------|-------|
| 4 | Analizar estructura de CSVs descargados | Mapear campos a modelo de datos |
| 5 | Crear repositorio Git con estructura base | Seguir plantilla v7 |
| 6 | Configurar PostgreSQL y migrations | Docker + Alembic |

### 🟢 Prioridad NORMAL (Mes 1)

| # | Tarea |
|---|-------|
| 7 | Implementar conectores (Prima primero) |
| 8 | API básica de consulta de viajes |
| 9 | Dashboard MVP con métricas básicas |
| 10 | Sincronización automática con Celery |

---

## 📎 Referencias

- [Uber Driver API](https://developer.uber.com/docs/drivers/introduction)
- [Portal FreeNow](https://portal.free-now.com/)
- [FreeNow Driver Help](https://driver.free-now.com/hc/es)
- [Taxitronic Prima](https://www.taxitronic.com/Control-taxis/)
- [Plantilla Desarrollo v7](./PLANTILLA_NUEVO_PROYECTO_v7.md)

---

> **Documento generado por Claude para Ivan Tintoré**
> **27 Enero 2026**
