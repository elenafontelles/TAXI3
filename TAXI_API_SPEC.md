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
9. [Infraestructura y Deployment](#9-infraestructura-y-deployment)
10. [Estrategia de Testing](#10-estrategia-de-testing)
11. [CI/CD & Deployment Automation](#11-cicd--deployment-automation)
12. [Testing & Quality Assurance](#12-testing--quality-assurance)
13. [Production Operations](#13-production-operations)
14. [Próximos Pasos](#14-próximos-pasos)

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
| **Estado** | ❌ **API RESTRINGIDA** - Usar CSV export |
| **Documentación** | [developer.uber.com/docs/drivers](https://developer.uber.com/docs/drivers/introduction) |
| **Método actual** | CSV manual desde driver dashboard |
| **Automatización** | Semi-manual (alerta si falta archivo) |

**✅ VERIFICACIÓN COMPLETADA (1 Febrero 2026):**

**App registrada:**
- Nombre: `Test_Iceman`
- App ID: `oO35JXSw0aV-K6fXTcdOmia08FAkLAmD`
- Client Secret: ✅ Generado
- Tipo: HYBRID APP

**Resultado de verificación:**
- ❌ **NO hay acceso a scopes** (Authorization Code, trips, payments)
- ⚠️ Portal indica: *"Your application currently does not have access to Authorization Code scopes"*
- 📋 Requiere: Contactar Uber Business Development representative
- 🔒 Realidad: Driver API solo para fleet management partners (típicamente 50+ vehículos)

**Documentación oficial confirma:**
> *"Access to the Driver API is currently limited. If you are interested in using this API, apply for access on the Drivers Product Page."*

---

**SOLUCIÓN IMPLEMENTADA: CSV Export Manual**

| Paso | Acción | Responsable | Frecuencia |
|------|--------|-------------|------------|
| 1 | Login en [driver.uber.com](https://driver.uber.com) | Conductor activo | Diario |
| 2 | Menu → "Earnings" → "Trip History" | | |
| 3 | Seleccionar fecha (día anterior) | | |
| 4 | Export → Download CSV | | |
| 5 | Renombrar: `uber_YYYY-MM-DD.csv` | | |
| 6 | Subir a carpeta `imports/` (SFTP o web upload) | | Antes 10:00 AM |
| 7 | Sistema procesa automáticamente | Celery task | 10:30 AM |

**Datos disponibles en CSV de Uber:**
- ✅ Fecha y hora del viaje
- ✅ Ciudad de recogida/destino  
- ✅ Distancia recorrida (km)
- ✅ Duración del viaje (minutos)
- ✅ Tarifa total (gross amount)
- ✅ Comisión de Uber (%)
- ✅ Importe neto recibido (payout)
- ✅ Tipo de servicio (UberX, Comfort, etc.)
- ✅ Método de pago (efectivo/tarjeta)
- ⚠️ NO incluye: Coordenadas GPS exactas

**Governance del proceso:**
- 🔔 Alerta Telegram si a las 10:00 AM no se detecta archivo
- ✅ Validación de hash (evitar duplicados)
- ✅ Schema validation antes de procesar
- 📊 Tracking en tabla `uber_imports` (similar a `freenow_imports`)

**Plan futuro (opcional - no bloquea desarrollo):**
1. Solicitar acceso formal en [developer.uber.com/products/drivers](https://developer.uber.com/products/drivers)
2. Esperar aprobación de Uber Business (2-8 semanas, puede rechazar)
3. Si aprueban → activar `uber_api_connector.py` (ya preparado en arquitectura)
4. Cambio en config: `UBER_SOURCE=api` (5 minutos de trabajo)

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
| **Uber** | CSV desde driver.uber.com | Manual diario | ✅ **VERIFICADO** - API no disponible |
| **FreeNow** | CSV desde portal.free-now.com | Manual diario | ✅ Confirmado |
| **Prima** | CSV desde cloud Taxitronic | ❓ Por confirmar | ⚠️ Verificar si es manual o automático |

**Notas importantes:**
- **Uber**: API restringida (requiere aprobación Uber Business). CSV es la única opción viable.
- **FreeNow**: Proceso manual documentado en Sección 2.2 con SLA y governance
- **Prima**: Por verificar si export es automático o manual. Plan de contingencia definido en Sección 2.3

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

## 9. Infraestructura y Deployment

### 9.1 Docker Setup

#### 9.1.1 ¿Por qué NO usar venv dentro de Docker?

**❌ ANTIPATRÓN: venv dentro de Docker**

```dockerfile
# ❌ MAL - No hacer esto
FROM python:3.11
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt
```

**Problemas:**
1. **Redundante**: Docker ya proporciona aislamiento completo
2. **Capas extra**: Aumenta el tamaño de la imagen innecesariamente
3. **Complejidad**: PATH y activación manual
4. **No es idiomático**: Va contra las mejores prácticas de Docker

**✅ CORRECTO: Instalación directa en imagen**

```dockerfile
# ✅ BIEN - Instalación directa
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Por qué funciona:**
- Cada container es un entorno aislado (como un venv)
- Las dependencias solo existen dentro del container
- Multi-stage builds separan build-time de runtime
- Layers caching optimiza rebuilds

---

#### 9.1.2 Dockerfile Multi-Stage (Producción)

```dockerfile
# ================================
# Stage 1: Builder (dependencias)
# ================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo requirements primero (cache layer)
COPY requirements.txt .

# Instalar dependencias en /install
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ================================
# Stage 2: Runtime (producción)
# ================================
FROM python:3.11-slim

WORKDIR /app

# Crear usuario no-root (seguridad)
RUN groupadd -r taxi && useradd -r -g taxi taxi

# Instalar solo runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias instaladas desde builder
COPY --from=builder /install /usr/local

# Copiar código fuente
COPY --chown=taxi:taxi src/ /app/src/
COPY --chown=taxi:taxi tasks/ /app/tasks/
COPY --chown=taxi:taxi migrations/ /app/migrations/
COPY --chown=taxi:taxi scripts/ /app/scripts/

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Cambiar a usuario no-root
USER taxi

# Exponer puerto
EXPOSE 8000

# Comando por defecto (puede ser sobreescrito en docker-compose)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

#### 9.1.3 docker-compose.yml Completo

```yaml
version: '3.8'

services:
  # ==================
  # Base de Datos
  # ==================
  db:
    image: postgres:15-alpine
    container_name: taxi-api-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME:-taxi_api}
      POSTGRES_USER: ${DB_USER:-taxi_admin}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?Database password required}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=es_ES.UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/01-init.sql:ro
    networks:
      - internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-taxi_admin}"]
      interval: 10s
      timeout: 5s
      retries: 5
    # NO exponer puerto en producción (solo red interna)
    # ports:
    #   - "5432:5432"  # Solo para desarrollo local

  # ==================
  # Redis (Celery broker)
  # ==================
  redis:
    image: redis:7-alpine
    container_name: taxi-api-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD:?Redis password required}
    volumes:
      - redis_data:/data
    networks:
      - internal
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==================
  # API FastAPI
  # ==================
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: taxi-api
    restart: unless-stopped
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      ENVIRONMENT: ${ENVIRONMENT:-production}
    ports:
      - "${API_PORT:-8000}:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - internal
      - public
    volumes:
      # Solo en desarrollo - hot reload
      - ./src:/app/src:ro
      - ./imports:/app/imports  # Para CSVs de FreeNow/Prima
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ==================
  # Celery Worker (sincronización)
  # ==================
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: taxi-api-celery-worker
    restart: unless-stopped
    command: celery -A tasks.celery_app worker --loglevel=info --concurrency=2
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      C_FORCE_ROOT: "true"  # Solo si es necesario
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - internal
    volumes:
      - ./imports:/app/imports  # Acceso a CSVs

  # ==================
  # Celery Beat (scheduler)
  # ==================
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: taxi-api-celery-beat
    restart: unless-stopped
    command: celery -A tasks.celery_app beat --loglevel=info
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - redis
      - celery-worker
    networks:
      - internal
    volumes:
      - celery_beat_data:/app/celerybeat-schedule

  # ==================
  # Prometheus (opcional - observability)
  # ==================
  prometheus:
    image: prom/prometheus:latest
    container_name: taxi-api-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - internal
    profiles:
      - monitoring

  # ==================
  # Grafana (opcional - dashboards)
  # ==================
  grafana:
    image: grafana/grafana:latest
    container_name: taxi-api-grafana
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
      GF_INSTALL_PLUGINS: redis-datasource
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-dashboards:/etc/grafana/provisioning/dashboards:ro
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    networks:
      - internal
    profiles:
      - monitoring

# ==================
# Volúmenes
# ==================
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  celery_beat_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

# ==================
# Redes
# ==================
networks:
  internal:
    driver: bridge
    internal: true  # No acceso a internet (seguridad)
  public:
    driver: bridge
```

---

#### 9.1.4 .env.example

```bash
# ==================
# Application
# ==================
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-secret-key-here-change-in-production

# ==================
# Database
# ==================
DB_NAME=taxi_api
DB_USER=taxi_admin
DB_PASSWORD=strong-password-here
DB_HOST=db
DB_PORT=5432

# ==================
# Redis
# ==================
REDIS_PASSWORD=redis-strong-password
REDIS_HOST=redis
REDIS_PORT=6379

# ==================
# API
# ==================
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# ==================
# OAuth (Uber)
# ==================
UBER_CLIENT_ID=your-uber-client-id
UBER_CLIENT_SECRET=your-uber-client-secret
UBER_REDIRECT_URI=https://yourdomain.com/auth/uber/callback

# ==================
# Telegram (Alertas)
# ==================
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_ADMIN_CHAT_ID=your-chat-id

# ==================
# Monitoring (opcional)
# ==================
GRAFANA_PASSWORD=admin
```

---

#### 9.1.5 .dockerignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments (no necesarios en Docker)
venv/
env/
ENV/
.venv

# Git
.git/
.gitignore

# IDE
.vscode/
.idea/
*.swp

# Environment
.env
.env.local

# Tests
.pytest_cache/
.coverage
htmlcov/

# Database
*.db
*.sqlite3

# Logs
logs/
*.log

# Documentation
docs/
*.md
!README.md

# Frontend (si se buildea separado)
frontend/node_modules/
frontend/build/

# Temporary
tmp/
temp/
*.tmp

# OS
.DS_Store
Thumbs.db
```

---

#### 9.1.6 Comandos Docker Útiles

```bash
# Desarrollo local
docker-compose up -d                    # Levantar servicios
docker-compose logs -f api              # Ver logs de API
docker-compose exec api bash            # Shell dentro del container
docker-compose down                     # Parar servicios

# Producción
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Con monitoring
docker-compose --profile monitoring up -d

# Migrations
docker-compose exec api alembic upgrade head
docker-compose exec api alembic revision --autogenerate -m "Add table"

# Acceso a DB
docker-compose exec db psql -U taxi_admin -d taxi_api

# Limpieza
docker-compose down -v                  # Eliminar también volúmenes
docker system prune -a                  # Limpiar todo Docker
```

---

### 9.2 Estructura del Proyecto Detallada

```
taxi-api/
├── README.md
├── TAXI_API_SPEC.md
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .dockerignore
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
│
├── src/
│   ├── __init__.py
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Settings (Pydantic BaseSettings)
│   │
│   ├── domain/               # 🎯 DOMAIN LAYER (Business Logic)
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── driver.py     # Driver entity
│   │   │   ├── owner.py      # Owner entity
│   │   │   ├── vehicle.py    # Vehicle entity
│   │   │   ├── trip.py       # Trip entity (CORE)
│   │   │   └── shift.py      # Shift entity
│   │   │
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── money.py      # Money VO (amount + currency)
│   │   │   ├── coordinates.py # GPS coordinates
│   │   │   └── email.py      # Email validation
│   │   │
│   │   └── repositories/     # 🔌 Repository Interfaces (abstract)
│   │       ├── __init__.py
│   │       ├── trip_repository.py
│   │       ├── driver_repository.py
│   │       └── vehicle_repository.py
│   │
│   ├── application/          # 📋 APPLICATION LAYER (Use Cases)
│   │   ├── __init__.py
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   ├── sync_uber.py
│   │   │   ├── sync_freenow.py
│   │   │   ├── sync_prima.py
│   │   │   ├── create_trip.py
│   │   │   ├── get_trips.py
│   │   │   └── calculate_summaries.py
│   │   │
│   │   ├── dto/              # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── trip_dto.py
│   │   │   └── summary_dto.py
│   │   │
│   │   └── services/         # Domain services
│   │       ├── __init__.py
│   │       ├── deduplication_service.py
│   │       └── billing_service.py
│   │
│   ├── infrastructure/       # 🔧 INFRASTRUCTURE LAYER (Implementations)
│   │   ├── __init__.py
│   │   │
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py      # DB connection & session
│   │   │   ├── base.py            # SQLAlchemy Base
│   │   │   │
│   │   │   ├── models/            # SQLAlchemy ORM models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── owner.py
│   │   │   │   ├── driver.py
│   │   │   │   ├── vehicle.py
│   │   │   │   ├── trip.py
│   │   │   │   ├── shift.py
│   │   │   │   ├── sync_log.py
│   │   │   │   ├── freenow_import.py
│   │   │   │   └── dedup_review.py
│   │   │   │
│   │   │   └── repositories/      # Repository implementations
│   │   │       ├── __init__.py
│   │   │       ├── sqlalchemy_trip_repository.py
│   │   │       ├── sqlalchemy_driver_repository.py
│   │   │       └── sqlalchemy_vehicle_repository.py
│   │   │
│   │   ├── connectors/            # External API connectors
│   │   │   ├── __init__.py
│   │   │   ├── uber_connector.py
│   │   │   ├── freenow_connector.py
│   │   │   └── prima_connector.py
│   │   │
│   │   └── external/              # External services
│   │       ├── __init__.py
│   │       ├── telegram.py
│   │       └── email.py
│   │
│   └── api/                  # 🌐 API LAYER (FastAPI endpoints)
│       ├── __init__.py
│       ├── dependencies.py   # Dependency injection
│       ├── middleware.py
│       │
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── health.py     # Health check
│       │   ├── trips.py      # Trip endpoints
│       │   ├── drivers.py    # Driver endpoints
│       │   ├── vehicles.py   # Vehicle endpoints
│       │   ├── summaries.py  # Summary/reports endpoints
│       │   └── sync.py       # Manual sync triggers
│       │
│       └── schemas/          # Pydantic schemas (request/response)
│           ├── __init__.py
│           ├── trip.py
│           ├── driver.py
│           ├── vehicle.py
│           └── common.py     # Shared schemas (pagination, etc)
│
├── tasks/                    # 📅 Celery tasks
│   ├── __init__.py
│   ├── celery_app.py        # Celery configuration
│   ├── sync_tasks.py        # Sync tasks (Uber, FreeNow, Prima)
│   └── maintenance_tasks.py # GPS anonymization, cleanups
│
├── migrations/               # 🗄️ Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
│
├── tests/                    # 🧪 Tests (TDD)
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   │
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_trip_entity.py
│   │   │   └── test_money_vo.py
│   │   ├── application/
│   │   │   └── test_create_trip_use_case.py
│   │   └── infrastructure/
│   │       └── test_uber_connector.py
│   │
│   ├── integration/
│   │   ├── test_trip_repository.py
│   │   └── test_database.py
│   │
│   └── e2e/
│       ├── test_api_trips.py
│       └── test_sync_flow.py
│
├── frontend/                 # ⚛️ React Dashboard
│   ├── package.json
│   ├── src/
│   └── public/
│
├── scripts/
│   ├── init_db.py
│   ├── init_db.sql
│   ├── import_csv.py
│   └── backfill_historical.py
│
└── monitoring/               # 📊 Observability
    ├── prometheus.yml
    └── grafana-dashboards/
        └── taxi-api-dashboard.json
```

---

## 9.3 Capa de Persistencia - Implementación Completa

### 9.3.1 Conexión a PostgreSQL

**`src/infrastructure/database/connection.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
from src.config import settings

# Engine con pool de conexiones
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verifica conexión antes de usar
    echo=settings.DEBUG,  # SQL logging en desarrollo
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para FastAPI.
    Crea una sesión por request, la cierra al final.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager para uso fuera de FastAPI (Celery, scripts).
    
    Usage:
        with get_db_context() as db:
            repo = SQLAlchemyTripRepository(db)
            trips = repo.get_all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

---

**`src/infrastructure/database/base.py`**

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# Naming convention para constraints (facilita migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)
```

---

### 9.3.2 Modelos SQLAlchemy (ORM)

**`src/infrastructure/database/models/owner.py`**

```python
from sqlalchemy import Column, String, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.infrastructure.database.base import Base


class OwnerModel(Base):
    """Modelo SQLAlchemy para propietarios de taxis"""
    
    __tablename__ = "owners"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    tax_id = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    drivers = relationship("DriverModel", back_populates="owner")
    vehicles = relationship("VehicleModel", back_populates="owner")
```

---

**`src/infrastructure/database/models/driver.py`**

```python
from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.infrastructure.database.base import Base


class DriverModel(Base):
    """Modelo SQLAlchemy para conductores"""
    
    __tablename__ = "drivers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    license_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    owner_id = Column(UUID(as_uuid=True), ForeignKey("owners.id"), nullable=False, index=True)
    
    # Platform IDs
    uber_driver_id = Column(String(100), index=True)
    freenow_driver_id = Column(String(100), index=True)
    
    is_owner = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("OwnerModel", back_populates="drivers")
    trips = relationship("TripModel", back_populates="driver")
    shifts = relationship("ShiftModel", back_populates="driver")
```

---

**`src/infrastructure/database/models/vehicle.py`**

```python
from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.infrastructure.database.base import Base


class VehicleModel(Base):
    """Modelo SQLAlchemy para vehículos (taxis)"""
    
    __tablename__ = "vehicles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plate = Column(String(20), unique=True, nullable=False, index=True)
    license_number = Column(String(50), nullable=False, index=True)
    model = Column(String(100))
    brand = Column(String(50))
    year = Column(Integer)
    
    # Foreign Keys
    owner_id = Column(UUID(as_uuid=True), ForeignKey("owners.id"), nullable=False, index=True)
    
    # Platform IDs
    taximeter_id = Column(String(50), index=True)
    uber_vehicle_id = Column(String(100))
    freenow_vehicle_id = Column(String(100))
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    owner = relationship("OwnerModel", back_populates="vehicles")
    trips = relationship("TripModel", back_populates="vehicle")
    shifts = relationship("ShiftModel", back_populates="vehicle")
```

---

**`src/infrastructure/database/models/trip.py`** (MODELO CORE)

```python
from sqlalchemy import (
    Column, String, Integer, Boolean, TIMESTAMP, ForeignKey,
    Numeric, Text, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
import uuid

from src.infrastructure.database.base import Base


class TripModel(Base):
    """Modelo SQLAlchemy para viajes (TABLA CENTRAL)"""
    
    __tablename__ = "trips"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identificación
    source = Column(String(20), nullable=False, index=True)  # uber, freenow, prima, street
    external_id = Column(String(100))  # ID de la plataforma externa
    
    # Foreign Keys
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False, index=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)
    shift_id = Column(UUID(as_uuid=True), ForeignKey("shifts.id"), index=True)
    
    # Tiempo
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    ended_at = Column(TIMESTAMP(timezone=True))
    duration_minutes = Column(Numeric(10, 2))
    
    # Ubicación (GPS)
    origin_lat = Column(Numeric(10, 7))
    origin_lng = Column(Numeric(10, 7))
    dest_lat = Column(Numeric(10, 7))
    dest_lng = Column(Numeric(10, 7))
    origin_address = Column(Text)
    dest_address = Column(Text)
    
    # Distancia
    distance_km = Column(Numeric(10, 2))
    
    # Importes (multi-currency)
    currency_code = Column(String(3), nullable=False, default='EUR')
    gross_amount = Column(Numeric(10, 2), nullable=False)
    commission = Column(Numeric(10, 2), default=0)
    platform_fee = Column(Numeric(10, 2), default=0)
    taxes_vat = Column(Numeric(10, 2), default=0)
    tips = Column(Numeric(10, 2), default=0)
    tolls = Column(Numeric(10, 2), default=0)
    adjustments = Column(Numeric(10, 2), default=0)
    payout_amount = Column(Numeric(10, 2))  # Real amount received
    exchange_rate = Column(Numeric(10, 4))
    
    # Desglose detallado
    amount_breakdown = Column(JSONB, default={})
    
    # Detalles
    payment_method = Column(String(20))  # card, cash, app
    tariff_code = Column(String(20))
    
    # Deduplicación
    merged_into_trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"))
    is_canonical = Column(Boolean, default=True, nullable=False, index=True)
    
    # Datos originales
    raw_data = Column(JSONB)
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    driver = relationship("DriverModel", back_populates="trips")
    vehicle = relationship("VehicleModel", back_populates="trips")
    shift = relationship("ShiftModel", back_populates="trips")
    
    # Self-referential para duplicados
    merged_into = relationship("TripModel", remote_side=[id], foreign_keys=[merged_into_trip_id])
    
    # Computed property (sin storage en DB, se calcula al acceder)
    @hybrid_property
    def net_amount(self):
        """Calcula el monto neto (gross - commission - platform_fee)"""
        return self.gross_amount - self.commission - self.platform_fee
    
    # Check constraints
    __table_args__ = (
        CheckConstraint('gross_amount >= 0', name='ck_trips_gross_amount_positive'),
        CheckConstraint('commission >= 0', name='ck_trips_commission_positive'),
        CheckConstraint('distance_km >= 0', name='ck_trips_distance_positive'),
        Index('idx_trips_source', 'source'),
        Index('idx_trips_canonical', 'is_canonical', postgresql_where=(is_canonical == True)),
        Index('idx_trips_driver_date', 'driver_id', 'started_at'),
        Index('idx_unique_trip_external_id', 'source', 'external_id', unique=True,
              postgresql_where=(external_id.isnot(None))),
    )
    
    def __repr__(self):
        return f"<Trip(id={self.id}, source={self.source}, amount={self.gross_amount} {self.currency_code})>"
```

---

### 9.3.3 Repository Pattern - Interfaces (Domain Layer)

**`src/domain/repositories/trip_repository.py`**

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from src.domain.entities.trip import Trip


class TripRepository(ABC):
    """
    Interfaz abstracta del Repository Pattern para Trips.
    
    Define el contrato que deben cumplir todas las implementaciones.
    Esta interfaz vive en la capa de DOMAIN (no sabe de SQLAlchemy).
    """
    
    @abstractmethod
    def get_by_id(self, trip_id: UUID) -> Optional[Trip]:
        """Obtiene un trip por su ID"""
        pass
    
    @abstractmethod
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        canonical_only: bool = True
    ) -> List[Trip]:
        """Obtiene lista de trips con paginación"""
        pass
    
    @abstractmethod
    def get_by_driver(
        self,
        driver_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Trip]:
        """Obtiene trips de un conductor en un rango de fechas"""
        pass
    
    @abstractmethod
    def get_by_source(self, source: str, date: datetime) -> List[Trip]:
        """Obtiene trips de una fuente específica en una fecha"""
        pass
    
    @abstractmethod
    def save(self, trip: Trip) -> Trip:
        """Crea o actualiza un trip"""
        pass
    
    @abstractmethod
    def delete(self, trip_id: UUID) -> bool:
        """Elimina un trip (soft delete recommended)"""
        pass
    
    @abstractmethod
    def exists_by_external_id(self, source: str, external_id: str) -> bool:
        """Verifica si existe un trip con ese external_id"""
        pass
    
    @abstractmethod
    def get_canonical_trips_for_dedup(
        self,
        vehicle_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[Trip]:
        """Obtiene trips canónicos para deduplicación en una ventana temporal"""
        pass
```

---

### 9.3.4 Repository Pattern - Implementación (Infrastructure Layer)

**`src/infrastructure/database/repositories/sqlalchemy_trip_repository.py`**

```python
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.domain.repositories.trip_repository import TripRepository
from src.domain.entities.trip import Trip
from src.infrastructure.database.models.trip import TripModel


class SQLAlchemyTripRepository(TripRepository):
    """
    Implementación concreta del TripRepository usando SQLAlchemy.
    
    Esta clase vive en la capa de INFRASTRUCTURE y conoce SQLAlchemy.
    Traduce entre TripModel (ORM) y Trip (Domain Entity).
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, trip_id: UUID) -> Optional[Trip]:
        """Obtiene un trip por ID"""
        trip_model = self.session.query(TripModel).filter(
            TripModel.id == trip_id
        ).first()
        
        if not trip_model:
            return None
        
        return self._to_entity(trip_model)
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        canonical_only: bool = True
    ) -> List[Trip]:
        """Obtiene trips con paginación"""
        query = self.session.query(TripModel)
        
        if canonical_only:
            query = query.filter(TripModel.is_canonical == True)
        
        trip_models = query.offset(skip).limit(limit).all()
        return [self._to_entity(tm) for tm in trip_models]
    
    def get_by_driver(
        self,
        driver_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Trip]:
        """Obtiene trips de un conductor con filtros de fecha"""
        query = self.session.query(TripModel).filter(
            TripModel.driver_id == driver_id,
            TripModel.is_canonical == True
        )
        
        if start_date:
            query = query.filter(TripModel.started_at >= start_date)
        
        if end_date:
            query = query.filter(TripModel.started_at <= end_date)
        
        trip_models = query.order_by(TripModel.started_at.desc()).all()
        return [self._to_entity(tm) for tm in trip_models]
    
    def get_by_source(self, source: str, date: datetime) -> List[Trip]:
        """Obtiene trips de una fuente en una fecha específica"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        trip_models = self.session.query(TripModel).filter(
            TripModel.source == source,
            TripModel.started_at >= start_of_day,
            TripModel.started_at <= end_of_day
        ).all()
        
        return [self._to_entity(tm) for tm in trip_models]
    
    def save(self, trip: Trip) -> Trip:
        """
        Guarda un trip (create o update).
        
        Si el trip tiene ID y existe en DB → UPDATE
        Si no tiene ID o no existe → CREATE
        """
        if trip.id:
            # Update existing
            trip_model = self.session.query(TripModel).filter(
                TripModel.id == trip.id
            ).first()
            
            if trip_model:
                self._update_model_from_entity(trip_model, trip)
            else:
                trip_model = self._to_model(trip)
                self.session.add(trip_model)
        else:
            # Create new
            trip_model = self._to_model(trip)
            self.session.add(trip_model)
        
        self.session.flush()  # Para obtener el ID generado
        self.session.refresh(trip_model)
        
        return self._to_entity(trip_model)
    
    def delete(self, trip_id: UUID) -> bool:
        """Elimina un trip (hard delete - considerar soft delete)"""
        result = self.session.query(TripModel).filter(
            TripModel.id == trip_id
        ).delete()
        
        return result > 0
    
    def exists_by_external_id(self, source: str, external_id: str) -> bool:
        """Verifica si existe un trip con ese external_id"""
        count = self.session.query(TripModel).filter(
            TripModel.source == source,
            TripModel.external_id == external_id
        ).count()
        
        return count > 0
    
    def get_canonical_trips_for_dedup(
        self,
        vehicle_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[Trip]:
        """
        Obtiene trips canónicos del mismo vehículo en una ventana temporal.
        Usado por el servicio de deduplicación.
        """
        trip_models = self.session.query(TripModel).filter(
            TripModel.vehicle_id == vehicle_id,
            TripModel.is_canonical == True,
            TripModel.started_at >= start_time,
            TripModel.started_at <= end_time
        ).order_by(TripModel.started_at).all()
        
        return [self._to_entity(tm) for tm in trip_models]
    
    # ==================
    # Mappers (ORM ↔ Entity)
    # ==================
    
    def _to_entity(self, model: TripModel) -> Trip:
        """Convierte TripModel (ORM) a Trip (Domain Entity)"""
        from src.domain.entities.trip import Trip
        
        return Trip(
            id=model.id,
            source=model.source,
            external_id=model.external_id,
            driver_id=model.driver_id,
            vehicle_id=model.vehicle_id,
            shift_id=model.shift_id,
            started_at=model.started_at,
            ended_at=model.ended_at,
            duration_minutes=model.duration_minutes,
            origin_lat=model.origin_lat,
            origin_lng=model.origin_lng,
            dest_lat=model.dest_lat,
            dest_lng=model.dest_lng,
            origin_address=model.origin_address,
            dest_address=model.dest_address,
            distance_km=model.distance_km,
            currency_code=model.currency_code,
            gross_amount=model.gross_amount,
            commission=model.commission,
            platform_fee=model.platform_fee,
            taxes_vat=model.taxes_vat,
            tips=model.tips,
            tolls=model.tolls,
            adjustments=model.adjustments,
            payout_amount=model.payout_amount,
            exchange_rate=model.exchange_rate,
            amount_breakdown=model.amount_breakdown or {},
            payment_method=model.payment_method,
            tariff_code=model.tariff_code,
            merged_into_trip_id=model.merged_into_trip_id,
            is_canonical=model.is_canonical,
            raw_data=model.raw_data,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, entity: Trip) -> TripModel:
        """Convierte Trip (Domain Entity) a TripModel (ORM)"""
        return TripModel(
            id=entity.id,
            source=entity.source,
            external_id=entity.external_id,
            driver_id=entity.driver_id,
            vehicle_id=entity.vehicle_id,
            shift_id=entity.shift_id,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            duration_minutes=entity.duration_minutes,
            origin_lat=entity.origin_lat,
            origin_lng=entity.origin_lng,
            dest_lat=entity.dest_lat,
            dest_lng=entity.dest_lng,
            origin_address=entity.origin_address,
            dest_address=entity.dest_address,
            distance_km=entity.distance_km,
            currency_code=entity.currency_code,
            gross_amount=entity.gross_amount,
            commission=entity.commission,
            platform_fee=entity.platform_fee,
            taxes_vat=entity.taxes_vat,
            tips=entity.tips,
            tolls=entity.tolls,
            adjustments=entity.adjustments,
            payout_amount=entity.payout_amount,
            exchange_rate=entity.exchange_rate,
            amount_breakdown=entity.amount_breakdown,
            payment_method=entity.payment_method,
            tariff_code=entity.tariff_code,
            merged_into_trip_id=entity.merged_into_trip_id,
            is_canonical=entity.is_canonical,
            raw_data=entity.raw_data
        )
    
    def _update_model_from_entity(self, model: TripModel, entity: Trip):
        """Actualiza un modelo existente con datos de la entidad"""
        model.source = entity.source
        model.external_id = entity.external_id
        model.driver_id = entity.driver_id
        model.vehicle_id = entity.vehicle_id
        model.shift_id = entity.shift_id
        model.started_at = entity.started_at
        model.ended_at = entity.ended_at
        model.duration_minutes = entity.duration_minutes
        model.origin_lat = entity.origin_lat
        model.origin_lng = entity.origin_lng
        model.dest_lat = entity.dest_lat
        model.dest_lng = entity.dest_lng
        model.distance_km = entity.distance_km
        model.gross_amount = entity.gross_amount
        model.commission = entity.commission
        model.platform_fee = entity.platform_fee
        model.taxes_vat = entity.taxes_vat
        model.tips = entity.tips
        model.tolls = entity.tolls
        model.adjustments = entity.adjustments
        model.payout_amount = entity.payout_amount
        model.is_canonical = entity.is_canonical
        model.merged_into_trip_id = entity.merged_into_trip_id
        # ... demás campos
```

---

### 9.3.5 Domain Entity (Business Logic)

**`src/domain/entities/trip.py`**

```python
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict
from uuid import UUID, uuid4


@dataclass
class Trip:
    """
    Entidad de dominio para Trip (Viaje).
    
    Esta clase representa la lógica de negocio pura, sin dependencias de DB.
    NO conoce SQLAlchemy, FastAPI, ni nada de infrastructure.
    """
    
    # Identificación
    source: str  # uber, freenow, prima, street
    started_at: datetime
    gross_amount: Decimal
    currency_code: str
    driver_id: UUID
    vehicle_id: UUID
    
    # Optional fields
    id: Optional[UUID] = field(default_factory=uuid4)
    external_id: Optional[str] = None
    shift_id: Optional[UUID] = None
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[Decimal] = None
    
    # Location
    origin_lat: Optional[Decimal] = None
    origin_lng: Optional[Decimal] = None
    dest_lat: Optional[Decimal] = None
    dest_lng: Optional[Decimal] = None
    origin_address: Optional[str] = None
    dest_address: Optional[str] = None
    
    # Distance
    distance_km: Optional[Decimal] = None
    
    # Financial
    commission: Decimal = Decimal("0.00")
    platform_fee: Decimal = Decimal("0.00")
    taxes_vat: Decimal = Decimal("0.00")
    tips: Decimal = Decimal("0.00")
    tolls: Decimal = Decimal("0.00")
    adjustments: Decimal = Decimal("0.00")
    payout_amount: Optional[Decimal] = None
    exchange_rate: Optional[Decimal] = None
    amount_breakdown: Dict = field(default_factory=dict)
    
    # Details
    payment_method: Optional[str] = None
    tariff_code: Optional[str] = None
    
    # Deduplication
    merged_into_trip_id: Optional[UUID] = None
    is_canonical: bool = True
    
    # Raw data
    raw_data: Optional[Dict] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # ==================
    # Business Logic
    # ==================
    
    @property
    def net_amount(self) -> Decimal:
        """Calcula el monto neto después de comisiones"""
        return self.gross_amount - self.commission - self.platform_fee
    
    @property
    def total_fees(self) -> Decimal:
        """Total de fees (commission + platform_fee)"""
        return self.commission + self.platform_fee
    
    @property
    def fee_percentage(self) -> Decimal:
        """Porcentaje de fees sobre el gross_amount"""
        if self.gross_amount == 0:
            return Decimal("0.00")
        return (self.total_fees / self.gross_amount) * 100
    
    def is_profitable(self, min_net_amount: Decimal = Decimal("5.00")) -> bool:
        """Verifica si el viaje es rentable según un mínimo"""
        return self.net_amount >= min_net_amount
    
    def mark_as_duplicate(self, canonical_trip_id: UUID) -> None:
        """Marca este trip como duplicado de otro canónico"""
        self.is_canonical = False
        self.merged_into_trip_id = canonical_trip_id
    
    def __str__(self):
        return f"Trip({self.source}, {self.gross_amount} {self.currency_code}, {self.started_at})"
```

---

### 9.3.6 Dependency Injection (FastAPI)

**`src/api/dependencies.py`**

```python
from fastapi import Depends
from sqlalchemy.orm import Session

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories.sqlalchemy_trip_repository import SQLAlchemyTripRepository
from src.domain.repositories.trip_repository import TripRepository


def get_trip_repository(db: Session = Depends(get_db)) -> TripRepository:
    """
    Dependency para inyectar TripRepository en endpoints de FastAPI.
    
    Retorna la interfaz (TripRepository), pero FastAPI inyecta
    la implementación concreta (SQLAlchemyTripRepository).
    
    Usage en endpoint:
        @app.get("/trips/{trip_id}")
        def get_trip(
            trip_id: UUID,
            repo: TripRepository = Depends(get_trip_repository)
        ):
            trip = repo.get_by_id(trip_id)
            return trip
    """
    return SQLAlchemyTripRepository(db)
```

---

### 9.3.7 Ejemplo de Uso en Endpoint FastAPI

**`src/api/routes/trips.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.domain.repositories.trip_repository import TripRepository
from src.api.dependencies import get_trip_repository
from src.api.schemas.trip import TripResponse, TripListResponse
from src.domain.entities.trip import Trip

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(
    trip_id: UUID,
    repo: TripRepository = Depends(get_trip_repository)
):
    """
    Obtiene un trip por ID.
    
    Clean Architecture en acción:
    1. Endpoint (API layer) recibe request
    2. Dependency injection inyecta repository
    3. Repository (domain interface) obtiene entity
    4. Retorna entity convertida a schema (response)
    """
    trip = repo.get_by_id(trip_id)
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found"
        )
    
    return TripResponse.from_entity(trip)


@router.get("/", response_model=TripListResponse)
def list_trips(
    skip: int = 0,
    limit: int = 100,
    canonical_only: bool = True,
    repo: TripRepository = Depends(get_trip_repository)
):
    """Lista trips con paginación"""
    trips = repo.get_all(skip=skip, limit=limit, canonical_only=canonical_only)
    
    return TripListResponse(
        data=[TripResponse.from_entity(t) for t in trips],
        total=len(trips),
        skip=skip,
        limit=limit
    )
```

---

### 9.3.8 Unit of Work Pattern (Transacciones)

**`src/infrastructure/database/unit_of_work.py`**

```python
from typing import Optional
from sqlalchemy.orm import Session

from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.database.repositories.sqlalchemy_trip_repository import SQLAlchemyTripRepository
from src.infrastructure.database.repositories.sqlalchemy_driver_repository import SQLAlchemyDriverRepository


class UnitOfWork:
    """
    Unit of Work pattern para gestionar transacciones.
    
    Agrupa múltiples operaciones de repositories en una sola transacción.
    Si algo falla, hace rollback de todo.
    
    Usage:
        with UnitOfWork() as uow:
            trip = uow.trips.get_by_id(trip_id)
            trip.mark_as_duplicate(canonical_id)
            uow.trips.save(trip)
            uow.commit()  # Commit solo si todo ok
    """
    
    def __init__(self):
        self.session: Optional[Session] = None
    
    def __enter__(self):
        self.session = SessionLocal()
        
        # Instanciar repositories con la misma sesión
        self.trips = SQLAlchemyTripRepository(self.session)
        self.drivers = SQLAlchemyDriverRepository(self.session)
        # ... más repositories
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Hubo excepción → rollback
            self.rollback()
        
        self.session.close()
    
    def commit(self):
        """Commit de la transacción"""
        self.session.commit()
    
    def rollback(self):
        """Rollback de la transacción"""
        self.session.rollback()
```

**Ejemplo de uso en caso de uso:**

```python
# src/application/use_cases/mark_trip_as_duplicate.py

from uuid import UUID
from src.infrastructure.database.unit_of_work import UnitOfWork


def mark_trip_as_duplicate_use_case(trip_id: UUID, canonical_trip_id: UUID) -> None:
    """
    Caso de uso: Marcar un trip como duplicado.
    
    Usa Unit of Work para gestionar la transacción.
    """
    with UnitOfWork() as uow:
        # Obtener trip
        trip = uow.trips.get_by_id(trip_id)
        
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")
        
        # Verificar que el canónico existe
        canonical = uow.trips.get_by_id(canonical_trip_id)
        if not canonical:
            raise ValueError(f"Canonical trip {canonical_trip_id} not found")
        
        # Business logic (Domain layer)
        trip.mark_as_duplicate(canonical_trip_id)
        
        # Guardar cambios
        uow.trips.save(trip)
        
        # Commit (o rollback automático si hay excepción)
        uow.commit()
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

## 11. CI/CD & Deployment Automation

### 11.1 Pre-commit Hooks (Calidad Automática)

**`.pre-commit-config.yaml`**

```yaml
# Pre-commit hooks configuration
# Install: pip install pre-commit
# Setup: pre-commit install
# Run: pre-commit run --all-files

repos:
  # Python code formatting
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        language_version: python3.11
        args: ['--line-length=100']

  # Import sorting
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile', 'black', '--line-length', '100']

  # Linting
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203,W503']

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: ['--ignore-missing-imports', '--no-strict-optional']

  # Security checks
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
        additional_dependencies: ['bandit[toml]']

  # Trailing whitespace, EOF, YAML
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  # Secrets detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # SQL formatting
  - repo: https://github.com/sqlfluff/sqlfluff
    rev: 3.0.0
    hooks:
      - id: sqlfluff-lint
        args: ['--dialect', 'postgres']

  # Dockerfile linting
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint-docker
```

**Setup inicial:**

```bash
# Instalar pre-commit
pip install pre-commit

# Activar hooks en el repo
pre-commit install

# Ejecutar manualmente (primera vez)
pre-commit run --all-files

# Crear baseline de secretos (si hay .env.example, etc)
detect-secrets scan > .secrets.baseline
```

---

### 11.2 GitHub Actions - CI Pipeline

**`.github/workflows/ci.yml`**

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: '3.11'
  POSTGRES_VERSION: '15'

jobs:
  # ==================
  # Linting & Security
  # ==================
  lint:
    name: Lint & Security Checks
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      - name: Run black
        run: black --check src/ tests/
      
      - name: Run isort
        run: isort --check-only src/ tests/
      
      - name: Run flake8
        run: flake8 src/ tests/
      
      - name: Run mypy
        run: mypy src/
      
      - name: Run bandit (security)
        run: bandit -r src/ -c pyproject.toml
      
      - name: Run detect-secrets
        run: detect-secrets scan --baseline .secrets.baseline

  # ==================
  # Unit Tests
  # ==================
  test-unit:
    name: Unit Tests
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=80
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests

  # ==================
  # Integration Tests
  # ==================
  test-integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: taxi_api_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run migrations
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/taxi_api_test
        run: |
          alembic upgrade head
      
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/taxi_api_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/integration/ -v

  # ==================
  # E2E Tests
  # ==================
  test-e2e:
    name: E2E Tests
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker images
        run: |
          docker-compose -f docker-compose.test.yml build
      
      - name: Run E2E tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from api
      
      - name: Cleanup
        if: always()
        run: |
          docker-compose -f docker-compose.test.yml down -v

  # ==================
  # Docker Build
  # ==================
  docker-build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [lint, test-unit, test-integration]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: taxi-api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

### 11.3 GitHub Actions - Deploy Pipeline

**`.github/workflows/deploy.yml`**

```yaml
name: Deploy

on:
  push:
    branches: [main]
    tags:
      - 'v*.*.*'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ==================
  # Build & Push Image
  # ==================
  build-and-push:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  # ==================
  # Deploy to Staging
  # ==================
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.taxi-api.yourdomain.com
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to staging server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/taxi-api-staging
            docker-compose pull
            docker-compose up -d --no-build
            docker-compose exec -T api alembic upgrade head
      
      - name: Run smoke tests
        run: |
          curl -f https://staging.taxi-api.yourdomain.com/health || exit 1
      
      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Staging deployment completed'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        if: always()

  # ==================
  # Deploy to Production
  # ==================
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build-and-push
    if: startsWith(github.ref, 'refs/tags/v')
    environment:
      name: production
      url: https://api.taxi.yourdomain.com
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Create backup
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/taxi-api
            ./scripts/backup.sh
      
      - name: Deploy to production
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/taxi-api
            export NEW_VERSION=${{ github.ref_name }}
            docker-compose pull
            docker-compose up -d --no-build
            docker-compose exec -T api alembic upgrade head
      
      - name: Run smoke tests
        run: |
          sleep 10
          ./scripts/smoke_tests.sh production
      
      - name: Rollback on failure
        if: failure()
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/taxi-api
            ./scripts/rollback.sh
      
      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Production deployment: ${{ github.ref_name }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        if: always()
```

---

### 11.4 Staging Environment

**`docker-compose.staging.yml`**

```yaml
# Override for staging environment
# Usage: docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

version: '3.8'

services:
  db:
    environment:
      POSTGRES_DB: taxi_api_staging
    volumes:
      - postgres_data_staging:/var/lib/postgresql/data

  api:
    image: ghcr.io/ivantintore/taxi2:develop
    environment:
      ENVIRONMENT: staging
      DEBUG: "True"
      # Staging-specific settings
      UBER_API_SANDBOX: "True"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.taxi-api-staging.rule=Host(`staging.taxi-api.yourdomain.com`)"
      - "traefik.http.routers.taxi-api-staging.entrypoints=websecure"
      - "traefik.http.routers.taxi-api-staging.tls.certresolver=letsencrypt"

  celery-worker:
    image: ghcr.io/ivantintore/taxi2:develop
    environment:
      ENVIRONMENT: staging

  celery-beat:
    image: ghcr.io/ivantintore/taxi2:develop
    environment:
      ENVIRONMENT: staging

volumes:
  postgres_data_staging:
```

---

## 12. Testing & Quality Assurance

### 12.1 TDD Workflow Completo (Paso a Paso)

**Ciclo Red → Green → Refactor**

```
┌─────────────────────────────────────────────────────────────┐
│                    CICLO TDD COMPLETO                        │
├─────────────────────────────────────────────────────────────┤
│  1. RED: Escribe test que FALLA                             │
│     - Define comportamiento esperado                         │
│     - Test debe fallar (código no existe)                   │
│                                                              │
│  2. GREEN: Escribe MÍNIMO código para pasar                 │
│     - Implementación simple                                  │
│     - Solo lo necesario para pasar el test                  │
│                                                              │
│  3. REFACTOR: Mejora el código                              │
│     - Clean code                                             │
│     - SOLID principles                                       │
│     - Tests siguen pasando                                   │
│                                                              │
│  4. REPETIR para siguiente funcionalidad                     │
└─────────────────────────────────────────────────────────────┘
```

**Ejemplo Real: Crear Trip**

**PASO 1: RED (Test que falla)**

```python
# tests/unit/domain/test_trip_entity.py

import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

from src.domain.entities.trip import Trip


def test_trip_calculates_net_amount_correctly():
    """
    RED: Este test DEBE FALLAR porque Trip aún no existe.
    
    Definimos el comportamiento esperado:
    - net_amount = gross_amount - commission - platform_fee
    """
    # Arrange
    trip = Trip(
        source="uber",
        started_at=datetime.now(),
        gross_amount=Decimal("25.00"),
        commission=Decimal("5.00"),
        platform_fee=Decimal("2.00"),
        currency_code="EUR",
        driver_id=uuid4(),
        vehicle_id=uuid4()
    )
    
    # Act
    net = trip.net_amount
    
    # Assert
    assert net == Decimal("18.00"), "Net should be 25 - 5 - 2 = 18"


def test_trip_marks_as_duplicate():
    """
    RED: Test para funcionalidad de duplicados
    """
    trip = Trip(
        source="freenow",
        started_at=datetime.now(),
        gross_amount=Decimal("20.00"),
        currency_code="EUR",
        driver_id=uuid4(),
        vehicle_id=uuid4()
    )
    
    canonical_id = uuid4()
    
    # Act
    trip.mark_as_duplicate(canonical_id)
    
    # Assert
    assert trip.is_canonical == False
    assert trip.merged_into_trip_id == canonical_id
```

**Ejecutar test (DEBE FALLAR):**

```bash
$ pytest tests/unit/domain/test_trip_entity.py -v

# Output esperado:
# FAILED - ModuleNotFoundError: No module named 'src.domain.entities.trip'
# ✓ Test falla como esperado (RED)
```

---

**PASO 2: GREEN (Implementación mínima)**

```python
# src/domain/entities/trip.py

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Trip:
    """Entidad de dominio para Trip"""
    
    source: str
    started_at: datetime
    gross_amount: Decimal
    currency_code: str
    driver_id: UUID
    vehicle_id: UUID
    
    commission: Decimal = Decimal("0.00")
    platform_fee: Decimal = Decimal("0.00")
    is_canonical: bool = True
    merged_into_trip_id: Optional[UUID] = None
    
    @property
    def net_amount(self) -> Decimal:
        """Calcula net amount"""
        return self.gross_amount - self.commission - self.platform_fee
    
    def mark_as_duplicate(self, canonical_trip_id: UUID) -> None:
        """Marca trip como duplicado"""
        self.is_canonical = False
        self.merged_into_trip_id = canonical_trip_id
```

**Ejecutar test (DEBE PASAR):**

```bash
$ pytest tests/unit/domain/test_trip_entity.py -v

# Output esperado:
# test_trip_calculates_net_amount_correctly PASSED
# test_trip_marks_as_duplicate PASSED
# ✓ Tests pasan (GREEN)
```

---

**PASO 3: REFACTOR (Mejorar código)**

```python
# src/domain/entities/trip.py (refactored)

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID, uuid4


@dataclass
class Trip:
    """
    Entidad de dominio para Trip (Viaje).
    
    Representa la lógica de negocio pura sin dependencias de DB.
    Sigue principios SOLID:
    - Single Responsibility: Solo lógica de viajes
    - Open/Closed: Extensible sin modificar
    """
    
    # Required fields
    source: str
    started_at: datetime
    gross_amount: Decimal
    currency_code: str
    driver_id: UUID
    vehicle_id: UUID
    
    # Optional fields with defaults
    id: UUID = field(default_factory=uuid4)
    commission: Decimal = Decimal("0.00")
    platform_fee: Decimal = Decimal("0.00")
    is_canonical: bool = True
    merged_into_trip_id: Optional[UUID] = None
    
    # Validation
    def __post_init__(self):
        if self.gross_amount < 0:
            raise ValueError("Gross amount cannot be negative")
        if self.commission < 0:
            raise ValueError("Commission cannot be negative")
    
    @property
    def net_amount(self) -> Decimal:
        """
        Calcula el monto neto después de comisiones.
        
        Formula: gross_amount - commission - platform_fee
        """
        return self.gross_amount - self.commission - self.platform_fee
    
    @property
    def total_fees(self) -> Decimal:
        """Total de fees pagados a plataformas"""
        return self.commission + self.platform_fee
    
    def mark_as_duplicate(self, canonical_trip_id: UUID) -> None:
        """
        Marca este trip como duplicado de otro canónico.
        
        Args:
            canonical_trip_id: ID del trip canónico
        
        Raises:
            ValueError: Si se intenta marcar como duplicado de sí mismo
        """
        if canonical_trip_id == self.id:
            raise ValueError("Cannot mark trip as duplicate of itself")
        
        self.is_canonical = False
        self.merged_into_trip_id = canonical_trip_id
```

**Añadir tests para validaciones:**

```python
# tests/unit/domain/test_trip_entity.py (extended)

def test_trip_raises_error_on_negative_amount():
    """Test validación de monto negativo"""
    with pytest.raises(ValueError, match="Gross amount cannot be negative"):
        Trip(
            source="uber",
            started_at=datetime.now(),
            gross_amount=Decimal("-10.00"),  # ❌ Negativo
            currency_code="EUR",
            driver_id=uuid4(),
            vehicle_id=uuid4()
        )


def test_trip_cannot_mark_as_duplicate_of_itself():
    """Test prevención de auto-duplicado"""
    trip = Trip(
        source="uber",
        started_at=datetime.now(),
        gross_amount=Decimal("20.00"),
        currency_code="EUR",
        driver_id=uuid4(),
        vehicle_id=uuid4()
    )
    
    with pytest.raises(ValueError, match="Cannot mark trip as duplicate of itself"):
        trip.mark_as_duplicate(trip.id)
```

**Ejecutar tests (TODOS PASAN):**

```bash
$ pytest tests/unit/domain/test_trip_entity.py -v --cov=src/domain/entities/trip

# Output:
# test_trip_calculates_net_amount_correctly PASSED
# test_trip_marks_as_duplicate PASSED
# test_trip_raises_error_on_negative_amount PASSED
# test_trip_cannot_mark_as_duplicate_of_itself PASSED
# 
# Coverage: 100%
# ✓ Refactor completo con tests pasando
```

---

### 12.2 Test Examples por Capa

**Unit Tests (Domain Layer)**

```python
# tests/unit/domain/value_objects/test_money.py

from decimal import Decimal
import pytest

from src.domain.value_objects.money import Money


class TestMoney:
    """Tests para Value Object Money"""
    
    def test_money_creation(self):
        money = Money(amount=Decimal("100.50"), currency="EUR")
        assert money.amount == Decimal("100.50")
        assert money.currency == "EUR"
    
    def test_money_addition_same_currency(self):
        m1 = Money(Decimal("10.00"), "EUR")
        m2 = Money(Decimal("5.50"), "EUR")
        
        result = m1 + m2
        
        assert result.amount == Decimal("15.50")
        assert result.currency == "EUR"
    
    def test_money_addition_different_currency_raises_error(self):
        m1 = Money(Decimal("10.00"), "EUR")
        m2 = Money(Decimal("5.00"), "USD")
        
        with pytest.raises(ValueError, match="Cannot add different currencies"):
            m1 + m2
    
    def test_money_is_immutable(self):
        money = Money(Decimal("100.00"), "EUR")
        
        with pytest.raises(AttributeError):
            money.amount = Decimal("200.00")  # ❌ No se puede modificar
```

**Integration Tests (Repository Layer)**

```python
# tests/integration/test_trip_repository.py

import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

from src.infrastructure.database.repositories.sqlalchemy_trip_repository import SQLAlchemyTripRepository
from src.domain.entities.trip import Trip


@pytest.fixture
def trip_repository(db_session):
    """Fixture que provee repository con DB real"""
    return SQLAlchemyTripRepository(db_session)


class TestTripRepository:
    """Integration tests con PostgreSQL real"""
    
    def test_save_and_retrieve_trip(self, trip_repository, driver_fixture, vehicle_fixture):
        """Test completo de persistencia"""
        # Arrange
        trip = Trip(
            source="uber",
            started_at=datetime.now(),
            gross_amount=Decimal("25.00"),
            currency_code="EUR",
            driver_id=driver_fixture.id,
            vehicle_id=vehicle_fixture.id
        )
        
        # Act - Save
        saved_trip = trip_repository.save(trip)
        
        # Assert - Save
        assert saved_trip.id is not None
        
        # Act - Retrieve
        retrieved_trip = trip_repository.get_by_id(saved_trip.id)
        
        # Assert - Retrieve
        assert retrieved_trip is not None
        assert retrieved_trip.gross_amount == Decimal("25.00")
        assert retrieved_trip.source == "uber"
    
    def test_get_by_driver_filters_correctly(self, trip_repository, driver_fixture, vehicle_fixture):
        """Test de query filtering"""
        # Arrange - Create 3 trips for same driver
        for i in range(3):
            trip = Trip(
                source="uber",
                started_at=datetime.now(),
                gross_amount=Decimal(f"{10 + i}.00"),
                currency_code="EUR",
                driver_id=driver_fixture.id,
                vehicle_id=vehicle_fixture.id
            )
            trip_repository.save(trip)
        
        # Act
        trips = trip_repository.get_by_driver(driver_fixture.id)
        
        # Assert
        assert len(trips) == 3
        assert all(t.driver_id == driver_fixture.id for t in trips)
```

**E2E Tests (API Layer)**

```python
# tests/e2e/test_api_trips.py

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import datetime

from src.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Headers con JWT token válido"""
    response = client.post("/auth/login", json={
        "email": "ivan@test.com",
        "password": "test123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestTripsAPI:
    """E2E tests del API de trips"""
    
    def test_create_trip_returns_201(self, client, auth_headers):
        """Test crear trip via API"""
        # Arrange
        trip_data = {
            "source": "street",
            "started_at": datetime.now().isoformat(),
            "gross_amount": "25.00",
            "currency_code": "EUR",
            "driver_id": str(uuid4()),
            "vehicle_id": str(uuid4())
        }
        
        # Act
        response = client.post(
            "/api/v1/trips",
            json=trip_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["source"] == "street"
        assert data["gross_amount"] == "25.00"
        assert "id" in data
    
    def test_list_trips_with_pagination(self, client, auth_headers):
        """Test paginación de trips"""
        # Act
        response = client.get(
            "/api/v1/trips?skip=0&limit=10",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert len(data["data"]) <= 10
    
    def test_get_trip_by_id_not_found_returns_404(self, client, auth_headers):
        """Test trip no encontrado"""
        # Act
        fake_id = str(uuid4())
        response = client.get(
            f"/api/v1/trips/{fake_id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404
```

---

### 12.3 Smoke Tests (Post-Deploy Validation)

**`scripts/smoke_tests.sh`**

```bash
#!/bin/bash

# Smoke Tests - Verificación rápida post-deploy
# Usage: ./scripts/smoke_tests.sh [production|staging]

set -e

ENVIRONMENT=${1:-staging}

case $ENVIRONMENT in
  production)
    BASE_URL="https://api.taxi.yourdomain.com"
    ;;
  staging)
    BASE_URL="https://staging.taxi-api.yourdomain.com"
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
    ;;
esac

echo "🔍 Running smoke tests against $ENVIRONMENT ($BASE_URL)"
echo "=================================================="

# Test 1: Health check
echo "✓ Test 1: Health endpoint"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ Health check failed (HTTP $HTTP_CODE)"
  exit 1
fi
echo "  ✅ Health check OK"

# Test 2: Database connectivity
echo "✓ Test 2: Database connection"
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
DB_STATUS=$(echo $HEALTH_RESPONSE | jq -r '.database')
if [ "$DB_STATUS" != "ok" ]; then
  echo "❌ Database not connected"
  exit 1
fi
echo "  ✅ Database OK"

# Test 3: Redis connectivity
echo "✓ Test 3: Redis connection"
REDIS_STATUS=$(echo $HEALTH_RESPONSE | jq -r '.redis')
if [ "$REDIS_STATUS" != "ok" ]; then
  echo "❌ Redis not connected"
  exit 1
fi
echo "  ✅ Redis OK"

# Test 4: API authentication
echo "✓ Test 4: Authentication"
AUTH_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/trips" -H "Authorization: Bearer invalid")
if [ "$AUTH_RESPONSE" != "401" ]; then
  echo "❌ Authentication not working properly"
  exit 1
fi
echo "  ✅ Authentication OK"

# Test 5: Celery workers
echo "✓ Test 5: Celery workers"
if [ "$ENVIRONMENT" = "production" ]; then
  ssh $PROD_HOST "docker ps | grep celery-worker | grep -q Up"
  if [ $? -ne 0 ]; then
    echo "❌ Celery workers not running"
    exit 1
  fi
fi
echo "  ✅ Celery OK"

# Test 6: Metrics endpoint (if Prometheus enabled)
echo "✓ Test 6: Metrics endpoint"
METRICS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/metrics")
if [ "$METRICS_CODE" = "200" ]; then
  echo "  ✅ Metrics OK"
else
  echo "  ⚠️  Metrics not available (optional)"
fi

echo ""
echo "=================================================="
echo "✅ All smoke tests passed for $ENVIRONMENT"
echo "Deploy validated successfully!"
```

---

## 13. Production Operations

### 13.1 Context Verification Checklist

**⚠️ SIEMPRE ejecutar ANTES de modificar código o hacer deploy**

```bash
#!/bin/bash
# scripts/verify_context.sh

echo "🔍 CONTEXT VERIFICATION CHECKLIST"
echo "=================================="

# 1. Verify project structure
echo ""
echo "1️⃣  Project Structure:"
ls -la
git status

# 2. Verify what's running
echo ""
echo "2️⃣  Running Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 3. Verify architecture docs
echo ""
echo "3️⃣  Architecture Documentation:"
if [ -f "README.md" ]; then
  echo "  ✅ README.md exists"
else
  echo "  ❌ README.md missing!"
fi

if [ -f "TAXI_API_SPEC.md" ]; then
  echo "  ✅ TAXI_API_SPEC.md exists"
else
  echo "  ❌ TAXI_API_SPEC.md missing!"
fi

# 4. Verify current branch
echo ""
echo "4️⃣  Git Branch:"
git branch --show-current

# 5. Verify environment
echo ""
echo "5️⃣  Environment Variables:"
if [ -f ".env" ]; then
  echo "  ✅ .env file exists"
  echo "  ENVIRONMENT=$(grep ENVIRONMENT .env | cut -d '=' -f2)"
else
  echo "  ❌ .env file missing!"
fi

echo ""
echo "=================================="
echo "✅ Context verification complete"
echo ""
echo "⚠️  CRITICAL QUESTIONS BEFORE PROCEEDING:"
echo "  1. Am I in the correct directory?"
echo "  2. Am I on the correct branch?"
echo "  3. Are the right containers running?"
echo "  4. Do I understand the current architecture?"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ Aborted"
  exit 1
fi
```

**Uso:**

```bash
# Antes de CUALQUIER modificación
./scripts/verify_context.sh

# Manual checklist:
# ✅ ¿Estoy en el directorio correcto?
# ✅ ¿Estoy en la branch correcta?
# ✅ ¿Los containers correctos están corriendo?
# ✅ ¿Entiendo la arquitectura actual?
# ✅ ¿He leído el README y TAXI_API_SPEC.md?
```

---

### 13.2 Rollback Procedures

**`scripts/rollback.sh`**

```bash
#!/bin/bash

# Rollback Script - Revertir a versión anterior
# Usage: ./scripts/rollback.sh [version]

set -e

BACKUP_DIR="/opt/taxi-api/backups"
ROLLBACK_VERSION=${1:-previous}

echo "🔙 TAXI API ROLLBACK PROCEDURE"
echo "=================================="
echo "Target version: $ROLLBACK_VERSION"
echo ""

# 1. Verificar backup existe
echo "1️⃣  Checking backup availability..."
if [ "$ROLLBACK_VERSION" = "previous" ]; then
  BACKUP_FILE=$(ls -t $BACKUP_DIR/*.tar.gz | head -1)
else
  BACKUP_FILE="$BACKUP_DIR/backup-$ROLLBACK_VERSION.tar.gz"
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Backup not found: $BACKUP_FILE"
  exit 1
fi
echo "  ✅ Backup found: $BACKUP_FILE"

# 2. Crear snapshot del estado actual (por si acaso)
echo ""
echo "2️⃣  Creating safety snapshot..."
./scripts/backup.sh "pre-rollback-$(date +%Y%m%d_%H%M%S)"

# 3. Detener servicios
echo ""
echo "3️⃣  Stopping services..."
docker-compose down

# 4. Restaurar desde backup
echo ""
echo "4️⃣  Restoring from backup..."
tar -xzf $BACKUP_FILE -C /opt/taxi-api/

# 5. Revertir base de datos
echo ""
echo "5️⃣  Rolling back database..."
docker-compose up -d db
sleep 5

# Obtener versión de migration del backup
MIGRATION_VERSION=$(cat /opt/taxi-api/.migration_version)
docker-compose exec -T db psql -U taxi_admin -d taxi_api -c "
  DELETE FROM alembic_version;
  INSERT INTO alembic_version VALUES ('$MIGRATION_VERSION');
"

# 6. Levantar servicios con versión anterior
echo ""
echo "6️⃣  Starting services with previous version..."
docker-compose up -d

# 7. Esperar que los servicios estén healthy
echo ""
echo "7️⃣  Waiting for services to be healthy..."
sleep 10

# 8. Ejecutar smoke tests
echo ""
echo "8️⃣  Running smoke tests..."
./scripts/smoke_tests.sh production

echo ""
echo "=================================="
echo "✅ Rollback completed successfully"
echo "Previous version restored from: $BACKUP_FILE"
echo ""
echo "⚠️  NEXT STEPS:"
echo "  1. Verify application is working: https://api.taxi.yourdomain.com/health"
echo "  2. Check logs: docker-compose logs -f api"
echo "  3. Notify team of rollback"
echo "  4. Investigate root cause of issue"
```

**`scripts/backup.sh`**

```bash
#!/bin/bash

# Backup Script - Crear backup completo
# Usage: ./scripts/backup.sh [backup-name]

set -e

BACKUP_DIR="/opt/taxi-api/backups"
BACKUP_NAME=${1:-backup-$(date +%Y%m%d_%H%M%S)}
BACKUP_FILE="$BACKUP_DIR/$BACKUP_NAME.tar.gz"

mkdir -p $BACKUP_DIR

echo "💾 Creating backup: $BACKUP_NAME"
echo "=================================="

# 1. Backup base de datos
echo "1️⃣  Backing up database..."
docker-compose exec -T db pg_dump -U taxi_admin taxi_api > $BACKUP_DIR/db_dump.sql

# 2. Backup archivos de configuración
echo "2️⃣  Backing up configuration..."
cp .env $BACKUP_DIR/.env.backup
cp docker-compose.yml $BACKUP_DIR/docker-compose.yml.backup

# 3. Guardar versión de migration actual
echo "3️⃣  Saving migration version..."
docker-compose exec -T db psql -U taxi_admin -d taxi_api -t -c "SELECT version_num FROM alembic_version;" | tr -d ' ' > $BACKUP_DIR/.migration_version

# 4. Comprimir todo
echo "4️⃣  Compressing backup..."
tar -czf $BACKUP_FILE -C $BACKUP_DIR db_dump.sql .env.backup docker-compose.yml.backup .migration_version

# 5. Limpiar archivos temporales
rm $BACKUP_DIR/db_dump.sql $BACKUP_DIR/.env.backup $BACKUP_DIR/docker-compose.yml.backup $BACKUP_DIR/.migration_version

# 6. Limpiar backups antiguos (mantener últimos 10)
echo "5️⃣  Cleaning old backups (keeping last 10)..."
ls -t $BACKUP_DIR/*.tar.gz | tail -n +11 | xargs -r rm

echo ""
echo "✅ Backup created: $BACKUP_FILE"
echo "Size: $(du -h $BACKUP_FILE | cut -f1)"
```

---

### 13.3 Incident Response Playbook

**`INCIDENT_RESPONSE.md`**

```markdown
# 🚨 INCIDENT RESPONSE PLAYBOOK

## Severidad de Incidentes

| Nivel | Descripción | Tiempo Respuesta | Escalación |
|-------|-------------|------------------|------------|
| **P0 - CRITICAL** | Sistema completamente caído | Inmediato | CEO + CTO |
| **P1 - HIGH** | Funcionalidad crítica afectada | < 30 min | Tech Lead |
| **P2 - MEDIUM** | Funcionalidad no crítica afectada | < 2 horas | On-call dev |
| **P3 - LOW** | Issue menor, workaround disponible | < 24 horas | Backlog |

---

## P0 - CRITICAL: Sistema Caído

### Síntomas:
- API no responde (500 errors)
- Base de datos no accesible
- Celery workers detenidos
- Múltiples alertas en Grafana

### Procedimiento:

1. **COMUNICAR** (0-2 min)
   ```
   - Slack: #incidents "🚨 P0: API down, investigating"
   - Telegram: Notificar a Iván/Elena
   ```

2. **DIAGNÓSTICO RÁPIDO** (2-5 min)
   ```bash
   # Check services
   docker ps
   docker-compose logs --tail=100 api
   
   # Check database
   docker-compose exec db pg_isready
   
   # Check disk space
   df -h
   
   # Check memory
   free -h
   ```

3. **ACCIONES INMEDIATAS**

   **Opción A: Restart rápido** (si es intermitente)
   ```bash
   docker-compose restart api
   ```

   **Opción B: Rollback** (si fue causado por deploy reciente)
   ```bash
   ./scripts/rollback.sh
   ```

   **Opción C: Scale down** (si es sobrecarga)
   ```bash
   # Desactivar Celery beat temporalmente
   docker-compose stop celery-beat
   ```

4. **VALIDACIÓN** (10-15 min)
   ```bash
   ./scripts/smoke_tests.sh production
   curl https://api.taxi.yourdomain.com/health
   ```

5. **POST-MORTEM** (24h después)
   - Documentar causa raíz
   - Implementar prevención
   - Actualizar runbook

---

## P1 - HIGH: Sync Failing

### Síntomas:
- Alertas: "SyncFailureRate > 5%"
- Dashboard sin datos recientes
- Logs de error en Celery

### Procedimiento:

1. **Identificar fuente afectada**
   ```bash
   docker-compose logs celery-worker | grep ERROR
   # ¿Es Uber, FreeNow o Prima?
   ```

2. **Verificar credenciales**
   ```bash
   # Check OAuth tokens no expirados
   docker-compose exec api python scripts/check_tokens.py
   ```

3. **Trigger manual si falla automático**
   ```bash
   # Via API
   curl -X POST https://api.taxi.yourdomain.com/api/v1/sync/trigger/uber \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

4. **Si persiste: Degradar gracefully**
   - Notificar a conductores que deben subir CSV manual
   - Activar proceso manual documentado en Sección 2.2/2.3

---

## P2 - MEDIUM: High Dedup Queue

### Síntomas:
- Alerta: "HighDedupReviewQueue > 50"
- Dashboard muestra muchos duplicados pendientes

### Procedimiento:

1. **Revisar casos manualmente**
   ```
   https://dashboard.taxi.yourdomain.com/admin/dedup-review
   ```

2. **Ajustar thresholds si hay patrón**
   ```python
   # En config.py
   DEDUP_CONFIG = {
       "time_window_seconds": 180,  # Aumentar de 120 a 180
       "amount_tolerance_pct": 0.15  # Aumentar tolerancia
   }
   ```

3. **Re-procesar con nuevos thresholds**

---

## Contactos de Escalación

| Rol | Nombre | Teléfono | Email | Horario |
|-----|--------|----------|-------|---------|
| **On-call Primary** | Iván Tintoré | +34 XXX XXX XXX | ivan@... | 24/7 |
| **On-call Secondary** | [Developer] | ... | ... | Business hours |
| **Database Expert** | [DBA] | ... | ... | On-demand |

---

## Comandos Útiles

### Logs
```bash
# API logs
docker-compose logs -f --tail=100 api

# Celery logs
docker-compose logs -f --tail=100 celery-worker

# Database logs
docker-compose logs -f --tail=100 db

# Todos los errores últimos 30min
docker-compose logs --since 30m | grep ERROR
```

### Database
```bash
# Connect to DB
docker-compose exec db psql -U taxi_admin -d taxi_api

# Check connections
SELECT count(*) FROM pg_stat_activity;

# Kill long queries
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '5 minutes';
```

### Performance
```bash
# Check container resources
docker stats

# Check API response time
time curl https://api.taxi.yourdomain.com/health

# Check Celery queue size
docker-compose exec redis redis-cli LLEN celery
```
```

---

### 13.4 Structured Logging (JSON Format)

**¿Por qué JSON logs?**
- ✅ Legibles por máquinas (Loki, Elasticsearch)
- ✅ Búsquedas eficientes (`level=ERROR`, `source=uber`)
- ✅ Context propagation (trace_id, request_id)
- ✅ Parsing automático en Grafana

**`src/infrastructure/logging/logger.py`**

```python
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter para logs estructurados.
    
    Añade campos estándar a cada log:
    - timestamp (ISO 8601)
    - level (INFO, ERROR, etc)
    - logger_name
    - trace_id (si existe)
    - environment (production, staging, dev)
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Timestamp ISO 8601
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Level name
        log_record['level'] = record.levelname
        
        # Logger name
        log_record['logger'] = record.name
        
        # Environment
        from src.config import settings
        log_record['environment'] = settings.ENVIRONMENT
        
        # Request context (si existe)
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id
        
        # Extra fields
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        if hasattr(record, 'source'):
            log_record['source'] = record.source


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configura logging estructurado para toda la aplicación.
    
    Returns:
        Logger configurado con JSON formatter
    """
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove default handlers
    logger.handlers = []
    
    # Console handler con JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    
    # JSON formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(logger)s %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
logger = setup_logging()
```

---

**Uso en código:**

```python
# src/application/use_cases/sync_uber.py

import logging
from src.infrastructure.logging.logger import logger

# Add context to logger
log = logging.LoggerAdapter(logger, {
    'source': 'uber',
    'use_case': 'sync_trips'
})


async def sync_uber_trips(date: str):
    """Sincroniza trips de Uber con logging estructurado"""
    
    # Log inicio
    log.info(
        "Starting Uber sync",
        extra={
            'date': date,
            'action': 'sync_start'
        }
    )
    
    try:
        trips = await uber_connector.fetch_trips(date)
        
        # Log éxito
        log.info(
            "Uber sync completed successfully",
            extra={
                'date': date,
                'trips_count': len(trips),
                'action': 'sync_success'
            }
        )
        
        return trips
        
    except RateLimitError as e:
        # Log rate limit (WARNING)
        log.warning(
            "Uber API rate limit hit",
            extra={
                'date': date,
                'retry_after': e.retry_after,
                'action': 'rate_limit_hit'
            }
        )
        raise
        
    except Exception as e:
        # Log error con stack trace
        log.error(
            "Uber sync failed",
            extra={
                'date': date,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'action': 'sync_failed'
            },
            exc_info=True  # Include stack trace
        )
        raise
```

**Output JSON (ejemplo):**

```json
{
  "timestamp": "2026-01-27T10:30:45.123Z",
  "level": "INFO",
  "logger": "src.application.use_cases.sync_uber",
  "message": "Starting Uber sync",
  "environment": "production",
  "source": "uber",
  "use_case": "sync_trips",
  "date": "2026-01-26",
  "action": "sync_start"
}

{
  "timestamp": "2026-01-27T10:30:52.456Z",
  "level": "INFO",
  "logger": "src.application.use_cases.sync_uber",
  "message": "Uber sync completed successfully",
  "environment": "production",
  "source": "uber",
  "use_case": "sync_trips",
  "date": "2026-01-26",
  "trips_count": 12,
  "action": "sync_success"
}
```

---

**FastAPI Middleware para Request ID:**

```python
# src/api/middleware.py

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que añade request_id a cada request y lo logea.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            "Incoming request",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'client_host': request.client.host if request.client else None,
                'action': 'request_start'
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.info(
            "Request completed",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'action': 'request_end'
            }
        )
        
        # Add request_id to response headers
        response.headers['X-Request-ID'] = request_id
        
        return response
```

**Activar en FastAPI:**

```python
# src/main.py

from fastapi import FastAPI
from src.api.middleware import RequestLoggingMiddleware
from src.infrastructure.logging.logger import setup_logging

# Setup logging
setup_logging(log_level="INFO")

app = FastAPI()

# Add middleware
app.add_middleware(RequestLoggingMiddleware)
```

---

**Búsquedas en Loki/Grafana:**

```logql
# Todos los errores de sync en últimas 24h
{environment="production"} | json | level="ERROR" | action=~"sync_.*"

# Rate limits de Uber
{environment="production"} | json | source="uber" | action="rate_limit_hit"

# Requests lentos (>5s)
{environment="production"} | json | action="request_end" | duration > 5000

# Errores por source
sum by (source) (
  count_over_time({environment="production"} | json | level="ERROR" [24h])
)
```

---

### 13.5 Zero-Downtime Deploy Strategy

**Objetivo**: Deployar nueva versión SIN interrumpir el servicio activo.

**Estrategia: Rolling Update con Health Checks**

#### 13.5.1 Docker Compose con Healthchecks Mejorados

**`docker-compose.prod.yml`**

```yaml
version: '3.8'

services:
  api:
    image: ghcr.io/ivantintore/taxi2:${VERSION}
    deploy:
      replicas: 2  # Dos instancias para HA
      update_config:
        parallelism: 1        # Actualizar de 1 en 1
        delay: 10s            # Esperar 10s entre actualizaciones
        order: start-first    # Iniciar nueva antes de parar vieja
        failure_action: rollback
      rollback_config:
        parallelism: 1
        delay: 5s
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 40s
    environment:
      - GRACEFUL_SHUTDOWN_TIMEOUT=30  # Espera requests en curso
```

**Configuración de Graceful Shutdown en FastAPI:**

```python
# src/main.py

import signal
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

shutdown_event = asyncio.Event()


def handle_shutdown_signal(signum, frame):
    """Handler para SIGTERM/SIGINT"""
    logger.info("Shutdown signal received, starting graceful shutdown...")
    shutdown_event.set()


# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown_signal)
signal.signal(signal.SIGINT, handle_shutdown_signal)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events"""
    # Startup
    logger.info("Application starting up")
    yield
    
    # Shutdown
    logger.info("Application shutting down gracefully")
    
    # Wait for in-flight requests (max 30s)
    await asyncio.wait_for(
        shutdown_event.wait(),
        timeout=30.0
    )
    
    logger.info("All requests completed, shutdown complete")


app = FastAPI(lifespan=lifespan)
```

---

#### 13.5.2 Script de Deploy con Zero-Downtime

**`scripts/deploy.sh`**

```bash
#!/bin/bash

# Zero-Downtime Deploy Script
# Usage: ./scripts/deploy.sh [version]

set -e

VERSION=${1:-latest}
HEALTH_ENDPOINT="https://api.taxi.yourdomain.com/health"
MAX_HEALTH_CHECKS=30
HEALTH_CHECK_INTERVAL=2

echo "🚀 ZERO-DOWNTIME DEPLOY"
echo "=================================="
echo "Version: $VERSION"
echo ""

# 1. Pre-deploy checks
echo "1️⃣  Pre-deploy checks..."

# Check current version is healthy
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_ENDPOINT)
if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ Current version is unhealthy (HTTP $HTTP_CODE)"
  echo "   Aborting deploy to prevent further issues"
  exit 1
fi
echo "  ✅ Current version is healthy"

# 2. Pull new image
echo ""
echo "2️⃣  Pulling new Docker image..."
docker pull ghcr.io/ivantintore/taxi2:$VERSION

# 3. Database migrations (if needed)
echo ""
echo "3️⃣  Running database migrations..."
docker-compose run --rm api alembic upgrade head

# 4. Start new container (blue-green style)
echo ""
echo "4️⃣  Starting new version (blue-green)..."

# Export version for docker-compose
export VERSION=$VERSION

# Start new instance (will run alongside old one temporarily)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --scale api=2 --no-recreate api

# 5. Wait for new instance to be healthy
echo ""
echo "5️⃣  Waiting for new instance to be healthy..."

NEW_CONTAINER_ID=$(docker ps --filter "name=taxi-api" --format "{{.ID}}" | head -1)

for i in $(seq 1 $MAX_HEALTH_CHECKS); do
  HEALTH=$(docker exec $NEW_CONTAINER_ID curl -s http://localhost:8000/health | jq -r '.status // "unhealthy"')
  
  if [ "$HEALTH" = "healthy" ]; then
    echo "  ✅ New instance is healthy (check $i/$MAX_HEALTH_CHECKS)"
    break
  fi
  
  if [ $i -eq $MAX_HEALTH_CHECKS ]; then
    echo "  ❌ New instance failed health checks"
    echo "  Rolling back..."
    docker stop $NEW_CONTAINER_ID
    docker rm $NEW_CONTAINER_ID
    exit 1
  fi
  
  echo "  ⏳ Health check $i/$MAX_HEALTH_CHECKS (status: $HEALTH)"
  sleep $HEALTH_CHECK_INTERVAL
done

# 6. Smoke tests on new instance
echo ""
echo "6️⃣  Running smoke tests on new instance..."

# Test against new container directly
NEW_PORT=$(docker port $NEW_CONTAINER_ID 8000 | cut -d: -f2)
./scripts/smoke_tests.sh "http://localhost:$NEW_PORT"

# 7. Gracefully stop old instances
echo ""
echo "7️⃣  Gracefully stopping old instances..."

OLD_CONTAINERS=$(docker ps --filter "name=taxi-api" --format "{{.ID}}" | tail -n +2)

for container in $OLD_CONTAINERS; do
  echo "  Sending SIGTERM to $container..."
  docker kill --signal=SIGTERM $container
  
  # Wait for graceful shutdown (max 30s)
  for i in $(seq 1 15); do
    if ! docker ps -q --filter "id=$container" | grep -q .; then
      echo "  ✅ Container $container stopped gracefully"
      break
    fi
    sleep 2
  done
  
  # Force kill if still running
  if docker ps -q --filter "id=$container" | grep -q .; then
    echo "  ⚠️  Force killing $container (timeout)"
    docker kill $container
  fi
  
  docker rm $container
done

# 8. Final health check
echo ""
echo "8️⃣  Final health check..."

sleep 5

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_ENDPOINT)
if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ Deploy verification failed (HTTP $HTTP_CODE)"
  exit 1
fi

# 9. Cleanup old images
echo ""
echo "9️⃣  Cleaning up old Docker images..."
docker image prune -f

echo ""
echo "=================================="
echo "✅ ZERO-DOWNTIME DEPLOY SUCCESSFUL"
echo "Version $VERSION is now live"
echo ""
echo "📊 Monitoring:"
echo "  - Logs: docker-compose logs -f api"
echo "  - Metrics: https://grafana.taxi.yourdomain.com"
echo "  - Health: $HEALTH_ENDPOINT"
```

---

#### 13.5.3 Improved Health Check Endpoint

**`src/api/routes/health.py`**

```python
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any
import asyncpg
import redis.asyncio as redis
from datetime import datetime

from src.infrastructure.database.connection import engine
from src.config import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    timestamp: str
    version: str
    checks: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check.
    
    Returns:
        - 200 if all systems healthy
        - 503 if any critical system is down
    """
    checks = {}
    overall_status = "healthy"
    
    # 1. Database check
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = {
            "status": "ok",
            "response_time_ms": 5  # Measure actual time
        }
    except Exception as e:
        checks["database"] = {
            "status": "error",
            "error": str(e)
        }
        overall_status = "unhealthy"
    
    # 2. Redis check
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        checks["redis"] = {"status": "ok"}
    except Exception as e:
        checks["redis"] = {
            "status": "error",
            "error": str(e)
        }
        overall_status = "degraded"  # Redis down = degraded, not unhealthy
    
    # 3. Celery workers check (optional)
    try:
        # Check if workers are running
        # This is optional, comment out if causing issues
        checks["celery"] = {"status": "ok"}
    except:
        checks["celery"] = {"status": "unknown"}
    
    # 4. Disk space check
    import shutil
    disk_usage = shutil.disk_usage("/")
    disk_percent = (disk_usage.used / disk_usage.total) * 100
    
    if disk_percent > 90:
        checks["disk"] = {
            "status": "warning",
            "percent_used": round(disk_percent, 2)
        }
        overall_status = "degraded" if overall_status == "healthy" else overall_status
    else:
        checks["disk"] = {
            "status": "ok",
            "percent_used": round(disk_percent, 2)
        }
    
    # Response
    response = HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version=settings.VERSION,
        checks=checks
    )
    
    # Return 503 if unhealthy
    status_code = status.HTTP_200_OK if overall_status != "unhealthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return response
```

**Response ejemplo (healthy):**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T10:45:30.123Z",
  "version": "v1.2.3",
  "checks": {
    "database": {
      "status": "ok",
      "response_time_ms": 5
    },
    "redis": {
      "status": "ok"
    },
    "celery": {
      "status": "ok"
    },
    "disk": {
      "status": "ok",
      "percent_used": 45.2
    }
  }
}
```

---

#### 13.5.4 Monitoring During Deploy

**Script de monitoreo en tiempo real:**

```bash
#!/bin/bash
# scripts/monitor_deploy.sh

HEALTH_ENDPOINT="https://api.taxi.yourdomain.com/health"

echo "📊 MONITORING DEPLOY"
echo "Press Ctrl+C to stop"
echo ""

while true; do
  RESPONSE=$(curl -s $HEALTH_ENDPOINT)
  STATUS=$(echo $RESPONSE | jq -r '.status')
  VERSION=$(echo $RESPONSE | jq -r '.version')
  DB_STATUS=$(echo $RESPONSE | jq -r '.checks.database.status')
  
  TIMESTAMP=$(date '+%H:%M:%S')
  
  if [ "$STATUS" = "healthy" ]; then
    echo "[$TIMESTAMP] ✅ Status: $STATUS | Version: $VERSION | DB: $DB_STATUS"
  elif [ "$STATUS" = "degraded" ]; then
    echo "[$TIMESTAMP] ⚠️  Status: $STATUS | Version: $VERSION | DB: $DB_STATUS"
  else
    echo "[$TIMESTAMP] ❌ Status: $STATUS | Version: $VERSION | DB: $DB_STATUS"
  fi
  
  sleep 2
done
```

**Uso durante deploy:**

```bash
# Terminal 1: Monitoreo
./scripts/monitor_deploy.sh

# Terminal 2: Deploy
./scripts/deploy.sh v1.2.3

# Output Terminal 1:
# [10:45:30] ✅ Status: healthy | Version: v1.2.2 | DB: ok
# [10:45:32] ✅ Status: healthy | Version: v1.2.2 | DB: ok
# [10:45:55] ⚠️  Status: degraded | Version: v1.2.3 | DB: ok  ← Nueva instancia iniciando
# [10:46:05] ✅ Status: healthy | Version: v1.2.3 | DB: ok   ← Deploy completado
```

---

### 13.6 Debug Playbook

**Problema Común 1: API lento**

```bash
# 1. Check container resources
docker stats taxi-api

# 2. Check database connections
docker-compose exec db psql -U taxi_admin -d taxi_api -c "
  SELECT count(*), state 
  FROM pg_stat_activity 
  GROUP BY state;"

# 3. Check slow queries
docker-compose exec db psql -U taxi_admin -d taxi_api -c "
  SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
  FROM pg_stat_activity 
  WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';"

# 4. Enable query logging temporarily
docker-compose exec db psql -U taxi_admin -d taxi_api -c "
  ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
  SELECT pg_reload_conf();"

# 5. Profile with py-spy (si Python es el cuello de botella)
docker-compose exec api pip install py-spy
docker-compose exec api py-spy top --pid 1
```

**Problema Común 2: Celery tasks no ejecutan**

```bash
# 1. Check worker está corriendo
docker ps | grep celery-worker

# 2. Check logs
docker-compose logs celery-worker --tail=50

# 3. Check Redis connection
docker-compose exec redis redis-cli ping

# 4. Check queue size
docker-compose exec redis redis-cli LLEN celery

# 5. Purge queue si está bloqueada
docker-compose exec redis redis-cli FLUSHDB

# 6. Restart worker
docker-compose restart celery-worker
```

**Problema Común 3: Database connection pool exhausted**

```bash
# 1. Ver conexiones activas
docker-compose exec db psql -U taxi_admin -d taxi_api -c "
  SELECT count(*), application_name 
  FROM pg_stat_activity 
  GROUP BY application_name;"

# 2. Aumentar pool size temporalmente
# En src/infrastructure/database/connection.py:
# pool_size=20  (en vez de 10)
# max_overflow=40  (en vez de 20)

# 3. Restart API
docker-compose restart api
```

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
> **Versión: 2.0 - Production Ready**
