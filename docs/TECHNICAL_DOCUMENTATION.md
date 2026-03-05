# TAXI2 - Documentacion Tecnica Completa

## Indice

1. [Descripcion Funcional](#1-descripcion-funcional)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Stack Tecnologico](#3-stack-tecnologico)
4. [Modelo de Datos](#4-modelo-de-datos)
5. [Flujo General de Datos](#5-flujo-general-de-datos)
6. [Ingesta de Datos: Scrapers Automaticos](#6-ingesta-de-datos-scrapers-automaticos)
7. [Ingesta de Datos: Carga Manual de Archivos](#7-ingesta-de-datos-carga-manual-de-archivos)
8. [Parsers de Archivos](#8-parsers-de-archivos)
9. [Calculo de Liquidacion (Settlement)](#9-calculo-de-liquidacion-settlement)
10. [Dashboard de KPIs](#10-dashboard-de-kpis)
11. [Deteccion de Incidencias](#11-deteccion-de-incidencias)
12. [Exportacion de Datos](#12-exportacion-de-datos)
13. [Autenticacion y Seguridad](#13-autenticacion-y-seguridad)
14. [API REST v1](#14-api-rest-v1)
15. [Sistema de Trabajos Asincronos](#15-sistema-de-trabajos-asincronos)
16. [Cumplimiento GDPR](#16-cumplimiento-gdpr)
17. [Despliegue y Operaciones](#17-despliegue-y-operaciones)
18. [Estructura de Archivos del Proyecto](#18-estructura-de-archivos-del-proyecto)

---

## 1. Descripcion Funcional

TAXI2 es un sistema integral de gestion de flotas de taxi que automatiza la recopilacion de datos de viajes desde multiples plataformas, calcula las liquidaciones diarias de los conductores y genera informes financieros. El sistema esta diseñado para propietarios de licencias de taxi que operan con multiples conductores y vehiculos.

### Funcionalidades principales

- **Agregacion multi-plataforma**: Recopila datos de viajes de Prima (taximetro), FreeNow (app de movilidad) y Uber
- **Importacion de datos financieros**: Extractos bancarios La Caixa (pagos TPV/VISA), gastos de combustible (Petroprix, Repsol), gastos manuales
- **Liquidacion diaria**: Calculo automatizado de la liquidacion conductor-propietario con comisiones escalonadas
- **Scraping automatico**: Descarga automatica de datos desde los portales de FreeNow y Prima mediante navegador headless
- **Deteccion de incidencias**: Identificacion automatica de viajes sospechosos (posibles tiquets nulos)
- **Dashboard de KPIs**: Metricas mensuales comparativas por conductor (ingresos, km, tasa de ocupacion, combustible)
- **Exportacion**: Generacion de informes de liquidacion en Excel y PDF
- **API REST**: Acceso programatico a viajes, conductores, vehiculos y resumenes
- **Gestion administrativa**: Alta/baja de conductores y vehiculos, configuracion de comisiones

### Usuarios del sistema

| Rol | Acceso | Funciones |
|-----|--------|-----------|
| **Propietario (admin)** | Total | Dashboard, liquidacion, subir archivos, sincronizar, administrar conductores/vehiculos, validar incidencias |
| **Conductor** | Limitado | Dashboard propio, consulta de viajes propios |

### Plataformas integradas

| Plataforma | Tipo de dato | Formato | Metodo de ingesta |
|------------|-------------|---------|-------------------|
| **Prima** (Taxitronic) | Viajes taximetro | CSV (;) | Scraper automatico + carga manual |
| **FreeNow** | Viajes app | CSV (,) | Scraper automatico + carga manual |
| **Uber** | Resumenes diarios | CSV (,) | Carga manual |
| **La Caixa** | Extracto bancario TPV | XLS/XLSX | Carga manual |
| **Petroprix** | Gastos combustible | CSV (,) | Carga manual |
| **Repsol/Solred** | Gastos combustible | XLSX | Carga manual |

---

## 2. Arquitectura del Sistema

### 2.1 Diagrama de arquitectura general

```mermaid
graph TB
    subgraph "Usuarios"
        ADMIN["Administrador/Propietario<br>(Navegador Web)"]
        DRIVER["Conductor<br>(Navegador Web)"]
        API_CLIENT["Cliente API<br>(Bearer Token)"]
    end

    subgraph "TAXI2 System"
        subgraph "Frontend"
            TEMPLATES["Jinja2 Templates<br>+ Bootstrap 5"]
        end

        subgraph "Backend (FastAPI)"
            MAIN["FastAPI App<br>(src/main.py)"]
            AUTH["Auth Router<br>JWT Cookie"]
            DASH["Dashboard"]
            LIQ["Liquidacion"]
            UPLOAD["Upload"]
            SYNC["Sync"]
            TRIPS["Trips"]
            ADMIN_R["Admin"]
            VALID["Validation"]
            EXPORT["Export"]
            API_V1["API v1"]
        end

        subgraph "Servicios"
            CALC["Settlement Calculator"]
            INCIDENT["Incident Detector"]
            EXCEL_EXP["Excel Exporter"]
            PDF_EXP["PDF Exporter"]
            JOB_SVC["Job Service"]
            AUTH_SVC["Auth Service"]
            TRIP_SVC["Trip Service"]
            GDPR_SVC["GDPR Service"]
        end

        subgraph "Parsers"
            FN_PARSER["FreeNow Parser"]
            PRIMA_PARSER["Prima Parser"]
            UBER_PARSER["Uber Parser"]
            LC_PARSER["La Caixa Parser"]
            PETRO_PARSER["Petroprix Parser"]
            REPSOL_PARSER["Repsol Parser"]
        end

        subgraph "Workers (Arq)"
            WORKER["Arq Worker<br>(src/workers/tasks.py)"]
        end

        subgraph "Scrapers (Playwright)"
            FN_SCRAPER["FreeNow Scraper"]
            PRIMA_SCRAPER["Prima Scraper"]
        end

        REDIS[("Redis<br>Cola de trabajos")]
        DB[("PostgreSQL<br>Base de datos")]
    end

    subgraph "Plataformas Externas"
        FN_PORTAL["FreeNow Portal<br>portal.free-now.com"]
        PRIMA_PORTAL["Prima Portal<br>prima.taxitronic.com"]
    end

    ADMIN --> MAIN
    DRIVER --> MAIN
    API_CLIENT --> API_V1

    MAIN --> AUTH
    MAIN --> DASH
    MAIN --> LIQ
    MAIN --> UPLOAD
    MAIN --> SYNC
    MAIN --> TRIPS
    MAIN --> ADMIN_R
    MAIN --> VALID
    MAIN --> EXPORT
    MAIN --> API_V1

    LIQ --> CALC
    LIQ --> EXCEL_EXP
    LIQ --> PDF_EXP
    VALID --> INCIDENT
    SYNC --> JOB_SVC
    JOB_SVC --> REDIS
    WORKER --> REDIS
    WORKER --> FN_SCRAPER
    WORKER --> PRIMA_SCRAPER
    WORKER --> DB

    FN_SCRAPER --> FN_PORTAL
    PRIMA_SCRAPER --> PRIMA_PORTAL

    UPLOAD --> FN_PARSER
    UPLOAD --> PRIMA_PARSER
    UPLOAD --> UBER_PARSER
    UPLOAD --> LC_PARSER
    UPLOAD --> PETRO_PARSER
    UPLOAD --> REPSOL_PARSER

    MAIN --> DB
    SYNC --> DB
    UPLOAD --> DB
    LIQ --> DB
    DASH --> DB
```

### 2.2 Diagrama de contenedores Docker

```mermaid
graph LR
    subgraph "Docker Compose"
        API["taxi-api<br>FastAPI + Uvicorn<br>Puerto 8000"]
        WORKER["taxi-worker<br>Arq Worker<br>+ Playwright"]
        REDIS["taxi-redis<br>Redis 7<br>Puerto 6379"]
        DB["taxi-db<br>PostgreSQL 16<br>Puerto 5432"]
    end

    API --> DB
    API --> REDIS
    WORKER --> DB
    WORKER --> REDIS
    API -.->|"Encola trabajos"| REDIS
    WORKER -.->|"Consume trabajos"| REDIS
```

---

## 3. Stack Tecnologico

| Componente | Tecnologia | Version |
|-----------|-----------|---------|
| **Lenguaje** | Python | 3.11+ |
| **Framework web** | FastAPI | 0.100+ |
| **ORM** | SQLAlchemy | 2.0 |
| **Migraciones** | Alembic | 1.12+ |
| **Base de datos** | PostgreSQL | 16 |
| **Cola de trabajos** | Arq (Redis) | 0.25+ |
| **Cache/Broker** | Redis | 7 |
| **Scraping** | Playwright | 1.40+ |
| **Templates** | Jinja2 | 3.1+ |
| **CSS** | Bootstrap | 5.3.3 |
| **Excel** | openpyxl | 3.1+ |
| **PDF** | fpdf2 | 2.7+ |
| **Auth** | PyJWT + bcrypt | - |
| **Rate Limiting** | slowapi | - |
| **Contenedores** | Docker + Docker Compose | - |
| **CI/CD** | GitHub Actions | - |
| **Servidor** | Uvicorn (ASGI) | - |

---

## 4. Modelo de Datos

### 4.1 Diagrama Entidad-Relacion

```mermaid
erDiagram
    OWNER ||--o{ DRIVER : "posee"
    OWNER ||--o{ VEHICLE : "posee"
    DRIVER ||--o{ TRIP : "realiza"
    VEHICLE ||--o{ TRIP : "es_usado_en"
    DRIVER ||--o{ FUEL_EXPENSE : "gasta"
    VEHICLE ||--o{ FUEL_EXPENSE : "consume"
    DRIVER ||--o{ OTHER_EXPENSE : "incurre"
    DRIVER ||--o{ FREENOW_ADJUSTMENT : "recibe"
    VEHICLE ||--o{ TPV_DAILY_TOTAL : "registra"
    VEHICLE ||--o{ UBER_DAILY_SUMMARY : "opera"
    TRIP ||--o| TRIP : "linked_trip"
    TRIP ||--o{ PENDING_VALIDATION : "requiere"
    TRIP ||--o{ VISA_PAYMENT : "pago_visa"
    DRIVER ||--o{ SHIFT : "trabaja"
    VEHICLE ||--o{ SHIFT : "es_usado_en"
    DRIVER ||--o{ PLATFORM_TOKEN : "tiene_token"

    OWNER {
        string id PK
        string name
        string tax_id UK
        string email
        string phone
        boolean is_active
    }

    DRIVER {
        string id PK
        string name
        string email UK
        string license_number UK
        string owner_id FK
        string password_hash
        boolean is_owner
        boolean is_active
        decimal prima_base_pct
        decimal prima_bonus_pct
        decimal commission_threshold
        decimal freenow_commission_driver_pct
        decimal uber_commission_driver_pct
        boolean fuel_deducted_from_driver
    }

    VEHICLE {
        string id PK
        string plate UK
        string license_number
        string brand
        string model
        int year
        string owner_id FK
        boolean is_active
    }

    TRIP {
        string id PK
        string source
        string external_id
        string driver_id FK
        string vehicle_id FK
        string shift_id FK
        datetime started_at
        datetime ended_at
        decimal distance_km
        decimal km_free
        decimal duration_minutes
        decimal gross_amount
        decimal commission
        decimal tips
        decimal tolls
        string payment_method
        string fare_type
        string linked_trip_id FK
    }

    TPV_DAILY_TOTAL {
        string id PK
        date date
        string vehicle_id FK
        string license_number
        decimal amount
        string source_file
    }

    UBER_DAILY_SUMMARY {
        string id PK
        date date
        string license_number
        string vehicle_id FK
        decimal t3_fixed
        decimal total_payment
        decimal total_earnings
        decimal taximeter
        string source_file
    }

    FUEL_EXPENSE {
        string id PK
        date date
        string vehicle_id FK
        string driver_id FK
        decimal liters
        decimal amount
        string provider
        string payment_method
        string source_file
    }

    OTHER_EXPENSE {
        string id PK
        date date
        string driver_id FK
        decimal amount
        string description
        string category
    }

    FREENOW_ADJUSTMENT {
        string id PK
        date date
        string driver_id FK
        decimal amount
        string adjustment_type
    }

    PENDING_VALIDATION {
        string id PK
        string trip_id FK
        string validation_type
        string status
        json details
    }

    VISA_PAYMENT {
        string id PK
        date date
        string vehicle_id FK
        string trip_id FK
        decimal amount
        string brand
        string source_file
    }

    SHIFT {
        string id PK
        string driver_id FK
        string vehicle_id FK
        string source
        datetime started_at
        datetime ended_at
        decimal total_earnings
    }

    SYNC_LOG {
        string id PK
        string source
        string status
        int records_created
        int records_skipped
        datetime started_at
        datetime completed_at
    }

    PLATFORM_TOKEN {
        string id PK
        string driver_id FK
        string platform
        string access_token_encrypted
        datetime expires_at
        boolean is_valid
    }

    FREENOW_IMPORT {
        string id PK
        string filename
        string file_hash UK
        string status
        int records_imported
    }
```

### 4.2 Descripcion de modelos clave

#### Driver (Conductor)
Contiene la configuracion de comisiones que determina como se calcula la liquidacion:
- `prima_base_pct`: Porcentaje base del conductor (ej: 40%)
- `prima_bonus_pct`: Porcentaje bonus si supera umbral (ej: 45%)
- `commission_threshold`: Umbral de recaudacion neta para bonus (ej: 300 EUR)
- `freenow_commission_driver_pct`: Si > 0, el conductor asume la comision de FreeNow
- `fuel_deducted_from_driver`: Si true, la gasolina se descuenta del anticipado

#### Trip (Viaje)
Registro unificado de viajes de todas las plataformas:
- `source`: "prima", "freenow" o "uber"
- `fare_type`: "FIXED" o "METERED" (solo FreeNow)
- `payment_method`: "CASH", "APP", "efectivo", "tarjeta"
- `linked_trip_id`: Enlace Prima ↔ FreeNow/Uber para evitar doble contabilidad

#### Formato de `license_number` del conductor
El campo `license_number` del conductor sigue el formato: `"361 - 0397MSS"` donde:
- `361` = Numero de licencia del taxi
- `0397MSS` = Matricula del vehiculo asociado

Este formato se usa para resolver automaticamente la relacion conductor ↔ vehiculo.

---

## 5. Flujo General de Datos

```mermaid
graph TD
    subgraph "Origenes de Datos"
        PRIMA_SRC["Prima<br>(Taximetro)"]
        FN_SRC["FreeNow<br>(App)"]
        UBER_SRC["Uber<br>(App)"]
        LC_SRC["La Caixa<br>(Banco)"]
        FUEL_SRC["Petroprix/Repsol<br>(Combustible)"]
        MANUAL["Entrada Manual<br>(Otros gastos /<br>Ajustes FreeNow)"]
    end

    subgraph "Metodo de Ingesta"
        SCRAPER["Scrapers<br>(Automatico)"]
        CSV_UPLOAD["Carga CSV/XLSX<br>(Manual)"]
        FORM["Formularios Web<br>(Manual)"]
    end

    subgraph "Parsers"
        P_PRIMA["Prima Parser"]
        P_FN["FreeNow Parser"]
        P_UBER["Uber Parser"]
        P_LC["La Caixa Parser"]
        P_FUEL["Petroprix/Repsol Parser"]
    end

    subgraph "Almacenamiento"
        T_TRIPS[("trips")]
        T_TPV[("tpv_daily_totals")]
        T_UBER[("uber_daily_summaries")]
        T_FUEL[("fuel_expenses")]
        T_OTHER[("other_expenses")]
        T_FN_ADJ[("freenow_adjustments")]
    end

    subgraph "Procesamiento"
        SETTLEMENT["Motor de Liquidacion<br>(settlement_calculator.py)"]
        KPI["Calculo KPIs<br>(dashboard.py)"]
        INCIDENT_D["Detector Incidencias<br>(incident_detector.py)"]
    end

    subgraph "Salida"
        WEB["Interfaz Web"]
        EXCEL["Excel (.xlsx)"]
        PDF["PDF"]
        REST["API REST"]
    end

    PRIMA_SRC --> SCRAPER
    FN_SRC --> SCRAPER
    PRIMA_SRC --> CSV_UPLOAD
    FN_SRC --> CSV_UPLOAD
    UBER_SRC --> CSV_UPLOAD
    LC_SRC --> CSV_UPLOAD
    FUEL_SRC --> CSV_UPLOAD
    MANUAL --> FORM

    SCRAPER --> P_PRIMA
    SCRAPER --> P_FN
    CSV_UPLOAD --> P_PRIMA
    CSV_UPLOAD --> P_FN
    CSV_UPLOAD --> P_UBER
    CSV_UPLOAD --> P_LC
    CSV_UPLOAD --> P_FUEL

    P_PRIMA --> T_TRIPS
    P_FN --> T_TRIPS
    P_UBER --> T_UBER
    P_LC --> T_TPV
    P_FUEL --> T_FUEL
    FORM --> T_OTHER
    FORM --> T_FN_ADJ

    T_TRIPS --> SETTLEMENT
    T_TPV --> SETTLEMENT
    T_UBER --> SETTLEMENT
    T_FUEL --> SETTLEMENT
    T_OTHER --> SETTLEMENT
    T_FN_ADJ --> SETTLEMENT
    T_TRIPS --> KPI
    T_UBER --> KPI
    T_FUEL --> KPI
    T_TRIPS --> INCIDENT_D

    SETTLEMENT --> WEB
    SETTLEMENT --> EXCEL
    SETTLEMENT --> PDF
    KPI --> WEB
    INCIDENT_D --> WEB
    T_TRIPS --> REST
```

---

## 6. Ingesta de Datos: Scrapers Automaticos

Los scrapers utilizan **Playwright** (navegador Chromium headless) para automatizar la descarga de datos desde los portales web de FreeNow y Prima.

### 6.1 Diagrama de secuencia: Sincronizacion FreeNow

```mermaid
sequenceDiagram
    participant Admin as Administrador
    participant FastAPI as FastAPI
    participant Redis as Redis
    participant Worker as Arq Worker
    participant Playwright as Playwright Browser
    participant FreeNow as portal.free-now.com
    participant DB as PostgreSQL

    Admin->>FastAPI: POST /sync/freenow<br>(start_date, end_date)
    FastAPI->>DB: Crear SyncLog (status=running)
    FastAPI->>Redis: Encolar job sync_freenow
    FastAPI-->>Admin: Redirect /sync (303)

    Worker->>Redis: Consumir job
    Worker->>Playwright: Lanzar Chromium headless
    Playwright->>FreeNow: Navegar a login
    Playwright->>FreeNow: Introducir credenciales
    Playwright->>FreeNow: Navegar a booking-history
    Playwright->>FreeNow: Configurar rango de fechas
    Playwright->>FreeNow: Click "Request bookings"
    FreeNow-->>Playwright: Notificacion de descarga
    Playwright->>FreeNow: Descargar ZIP
    Playwright-->>Worker: CSV extraido

    Worker->>Worker: parse_freenow_csv()
    Worker->>DB: Crear Trip records
    Worker->>Worker: detect_incidents()
    Worker->>DB: Crear PendingValidation
    Worker->>DB: Actualizar SyncLog (status=success)
```

### 6.2 Diagrama de secuencia: Sincronizacion Prima

```mermaid
sequenceDiagram
    participant Admin as Administrador
    participant FastAPI as FastAPI
    participant Redis as Redis
    participant Worker as Arq Worker
    participant Playwright as Playwright Browser
    participant Prima as prima.taxitronic.com
    participant DB as PostgreSQL

    Admin->>FastAPI: POST /sync/prima<br>(start_date, end_date)
    FastAPI->>DB: Crear SyncLog (status=running)
    FastAPI->>Redis: Encolar job sync_prima
    FastAPI-->>Admin: Redirect /sync (303)

    Worker->>Redis: Consumir job
    Worker->>Playwright: Lanzar Chromium headless
    Playwright->>Prima: Navegar a login
    Playwright->>Prima: Introducir credenciales
    Playwright->>Prima: Navegar a ConsultaTurnos
    Playwright->>Prima: Seleccionar vehiculos y rango
    Playwright->>Prima: Click Buscar
    Playwright->>Prima: Exportar Servicios CSV
    Prima-->>Playwright: Descarga CSV
    Playwright-->>Worker: CSV descargado

    Worker->>Worker: parse_prima_csv()
    Worker->>DB: Crear Trip records
    Worker->>Worker: detect_incidents()
    Worker->>DB: Crear PendingValidation
    Worker->>DB: Actualizar SyncLog (status=success)
```

### 6.3 Soporte Multi-Cuenta FreeNow

El sistema soporta multiples cuentas de FreeNow porque las licencias de taxi estan distribuidas en diferentes cuentas:

| Cuenta | Etiqueta | Licencias |
|--------|----------|-----------|
| Cuenta 1 | `account1` | 092, 1061 |
| Cuenta 2 | `account2` | 361 |

La configuracion se gestiona en `src/config.py` mediante `Settings.get_freenow_accounts()`, que devuelve la lista de cuentas con sus credenciales.

---

## 7. Ingesta de Datos: Carga Manual de Archivos

### 7.1 Flujo general de carga de archivos

```mermaid
graph TD
    A["Admin selecciona archivo<br>y plataforma"] --> B{Plataforma?}

    B -->|"freenow / prima"| C["Guardar en temp"]
    B -->|"lacaixa"| D["_process_lacaixa()"]
    B -->|"uber"| E["_process_uber()"]
    B -->|"petroprix / repsol"| F["_process_fuel()"]

    C --> G["validate_csv_schema()"]
    G -->|Valido| H["parser(tmp_path)"]
    G -->|Invalido| ERR["Error: columnas faltantes"]
    H --> I["_build_lookups()"]
    I --> J["Resolver conductor/vehiculo<br>por cada registro"]
    J --> K["Eliminar trips anteriores<br>en rango de fechas"]
    K --> L["Crear Trip records"]
    L --> M["detect_incidents()"]
    M --> N["Resultado:<br>creados / reemplazados / sin asignar"]

    D --> D1["parse_lacaixa_xlsx()"]
    D1 --> D2["Eliminar TpvDailyTotal<br>en rango"]
    D2 --> D3["Crear TpvDailyTotal records"]

    E --> E1["parse_uber_csv()"]
    E1 --> E2["Resolver conductores"]
    E2 --> E3["Eliminar UberDailySummary<br>en rango"]
    E3 --> E4["Crear UberDailySummary records"]

    F --> F1["parse_petroprix_csv() /<br>parse_repsol_pdf()"]
    F1 --> F2["Eliminar FuelExpense<br>en rango"]
    F2 --> F3["Crear FuelExpense records"]
```

### 7.2 Resolucion automatica de conductor y vehiculo

El sistema resuelve automaticamente la asignacion de conductor y vehiculo a partir de los metadatos del archivo:

```mermaid
graph TD
    REC["Registro CSV"] --> A{Tiene _driver_name?}

    A -->|Si| B["Match por nombre<br>(case-insensitive, parcial)"]
    A -->|No| C{Tiene _license?}

    B --> D{Match encontrado?}
    D -->|Si| E["driver_id resuelto"]
    D -->|No| C

    C -->|Si| F["Match por licencia<br>(092, 361, 1061)"]
    C -->|No| G{Tiene _plate?}

    F --> H["driver_id + vehicle_id"]

    G -->|Si| I["Match por matricula<br>(normalizacion sin espacios)"]
    G -->|No| J["Usar fallback<br>(seleccion manual)"]

    I --> K{Match encontrado?}
    K -->|Si| L["vehicle_id resuelto"]
    K -->|No| J

    E --> M{vehicle_id?}
    M -->|No| N["Buscar via<br>driver_id_to_vehicle"]
    M -->|Si| O["Completo"]
    N --> O

    L --> P{driver_id?}
    P -->|No| Q["Buscar via<br>vehicle_id_to_driver"]
    P -->|Si| O
    Q --> O
```

### 7.3 Estrategia de reemplazo de datos

Al subir un nuevo archivo, el sistema **reemplaza** los datos existentes del mismo tipo en el rango de fechas del archivo:

| Tipo de dato | Clave de deduplicacion | Accion |
|-------------|----------------------|--------|
| Trips (FreeNow/Prima) | source + rango de fechas | DELETE anteriores en rango, INSERT nuevos |
| UberDailySummary | license_number + rango de fechas | DELETE anteriores, INSERT nuevos |
| TpvDailyTotal | license_number + rango de fechas | DELETE anteriores, INSERT nuevos |
| FuelExpense | vehicle_id + provider + rango de fechas | DELETE anteriores, INSERT nuevos |
| FreenowAdjustment | driver_id + date + adjustment_type | DELETE anterior, INSERT nuevo |
| OtherExpense | Sin reemplazo | Solo INSERT (acumulativo) |

### 7.4 Entrada manual: Otros Gastos

Formulario para registrar gastos no recurrentes del conductor:
- **Ruta**: `POST /upload/otros-gastos`
- **Campos**: conductor, fecha (DD/MM/YY), importe (EUR), concepto
- **Almacenamiento**: Tabla `other_expenses`, categoria "otro"

### 7.5 Entrada manual: Ajustes FreeNow (Otros/Incentivos)

Formulario para registrar bonificaciones e incentivos de FreeNow:
- **Ruta**: `POST /upload/freenow-ajustes`
- **Campos**: conductor, fecha_otros + importe_otros, fecha_incentivos + importe_incentivos
- **Tipos**: `otros` (cargos adicionales), `incentivos` (bonificaciones)
- **Comportamiento**: Cada nuevo valor **reemplaza** al anterior para el mismo conductor+fecha+tipo
- **Permite valor 0**: Para eliminar un ajuste previamente registrado

---

## 8. Parsers de Archivos

### 8.1 FreeNow Parser (`scripts/parsers/freenow_parser.py`)

| Aspecto | Detalle |
|---------|---------|
| **Formato** | CSV, delimitador: coma |
| **Encoding** | UTF-8 |
| **Filtro** | Solo filas con `BOOKING STATE = "ACCOMPLISHED"` |
| **Fechas** | ISO 8601 con timezone (ej: `2026-02-01T08:30:00+01:00`) |
| **Decimales** | Punto como separador |

**Columnas requeridas:**

| Columna CSV | Campo Trip | Descripcion |
|------------|-----------|-------------|
| BOOKING ID | external_id | ID unico del viaje |
| TOUR VALUE | gross_amount | Importe bruto del viaje |
| TOUR TIP | tips | Propina |
| TOLL VALUE | tolls | Peajes |
| TAX PERCENTAGE | taxes_vat | Porcentaje IVA |
| PICKUP DATE | started_at | Fecha/hora inicio |
| CLOSED DATE | ended_at | Fecha/hora fin |
| PAYMENT METHOD | payment_method | "CASH" o "APP" |
| FARE TYPE | fare_type | "FIXED" o "METERED" |
| DRIVER FIRST NAME + LAST NAME | _driver_name | Para resolucion automatica |
| LICENCE PLATE | _plate | Para resolucion automatica |

**Distincion FIXED vs METERED:**
- **FIXED**: FreeNow cobra tarifa fija. Se incluye en recaudacion como ingreso adicional al taximetro.
- **METERED**: FreeNow usa el taximetro. El importe ya esta registrado en Prima. No se suma a recaudacion para evitar duplicidad.

### 8.2 Prima Parser (`scripts/parsers/prima_parser.py`)

| Aspecto | Detalle |
|---------|---------|
| **Formato** | CSV, delimitador: punto y coma (;) |
| **Encoding** | UTF-8 |
| **Fechas** | `DD/MM/YYYY H:MM:SS` o `DD/MM/YY H:MM` (naive, sin timezone) |
| **Decimales** | Coma como separador (formato europeo) |

**Columnas requeridas:**

| Columna CSV | Campo Trip | Descripcion |
|------------|-----------|-------------|
| TripNumber | external_id | Numero de viaje |
| DateTripStart | started_at | Fecha/hora inicio (naive) |
| DateTripEnd | ended_at | Fecha/hora fin |
| AmountTotalPaid | gross_amount | Importe total |
| AmountTips | tips | Propinas |
| AmountTolls | tolls | Peajes |
| PaymentMode | payment_method | Modo de pago |
| km | distance_km | Km ocupados |
| km_free | km_free | Km en vacio |
| DriverName | _driver_name | Mapa conductor (1→NOMBRE) |
| License | _license | Numero licencia |

**Mapa de conductores Prima:**
El CSV de Prima usa codigos numericos para conductores (ej: "1", "2"). El parser mantiene un mapa interno que traduce estos codigos a nombres completos.

### 8.3 Uber Parser (`scripts/parsers/uber_parser.py`)

| Aspecto | Detalle |
|---------|---------|
| **Formato** | CSV, delimitador: coma |
| **Encoding** | UTF-8-sig (con BOM) |
| **Fechas** | Formato fecha en columna |
| **Salida** | Lista de resumenes diarios (no viajes individuales) |

**Campos de salida:**

| Campo | Descripcion |
|-------|-------------|
| date | Fecha del resumen |
| _driver_name | Nombre del conductor |
| t3_fixed | Ganancias - Taximetro (importe que suma a recaudacion) |
| total_payment | Pago total de Uber al conductor |
| total_earnings | Ganancias totales |

**Nota**: Uber no genera registros `Trip` individuales. Genera registros `UberDailySummary` con totales diarios por licencia.

### 8.4 La Caixa Parser (`scripts/parsers/lacaixa_parser.py`)

| Aspecto | Detalle |
|---------|---------|
| **Formato** | XLS o XLSX (extracto bancario) |
| **Deteccion** | Celda (1,1) contiene "Moviments del compte" |
| **Filtro** | Movimientos que empiezan por ON34, ON35 o ON36 |

**Mapeo de terminales a licencias:**

| Prefijo terminal | Licencia |
|-----------------|----------|
| ON34 (34) | 092 |
| ON35 (35) | 1061 |
| ON36 (36) | 361 |

**Salida:** Lista de `{date, license_number, amount}` agregados por dia y licencia.

### 8.5 Petroprix Parser (`scripts/parsers/petroprix_parser.py`)

| Aspecto | Detalle |
|---------|---------|
| **Formato** | CSV, delimitador: coma |
| **Decimales** | Europeo (coma en posicion de columnas) |
| **Fecha** | `DD-MM-YYYY HH:MM:SS` |

**Salida:** `FuelExpense` con date, _plate, liters, amount, provider="petroprix", payment_method

### 8.6 Repsol/Solred Parser (`scripts/parsers/repsol_parser.py`)

| Aspecto | Detalle |
|---------|---------|
| **Formato** | XLSX |
| **Litros** | Formato "39,120 l" o "43.81" |
| **Importe** | Numerico o con coma |

**Salida:** `FuelExpense` con date, _plate, liters, amount, provider="repsol", payment_method

---

## 9. Calculo de Liquidacion (Settlement)

El sistema de liquidacion es el nucleo financiero de la aplicacion. Calcula diariamente cuanto debe cobrar o pagar cada conductor al propietario.

### 9.1 Diagrama del flujo de calculo

```mermaid
graph TD
    subgraph "Datos de Entrada (por dia)"
        IN1["prima_amount<br>Taximetro"]
        IN2["freenow_fixed_bruto<br>FreeNow FIXED bruto"]
        IN3["freenow_fixed_tips<br>Propinas FreeNow"]
        IN4["uber_t3_fixed<br>Uber T3"]
        IN5["incidents_amount<br>Incidencias"]
        IN6["tpv_visa_total<br>Pagos TPV/VISA"]
        IN7["freenow_app_paid_bruto<br>FreeNow APP bruto"]
        IN8["freenow_app_tips<br>Propinas APP"]
        IN9["freenow_cash_bruto<br>FreeNow CASH bruto"]
        IN10["uber_total_payment<br>Pago Uber"]
        IN11["fuel_total<br>Gasolina"]
        IN12["other_expenses_total<br>Otros gastos"]
        IN13["freenow_adjustments<br>Ajustes FreeNow"]
    end

    subgraph "Paso 1: FreeNow Fixed (neto o bruto)"
        S1{"freenow_commission<br>_driver_pct > 0?"}
        S1 -->|"Si (conductor asume)"| S1A["freenow_fixed =<br>net(bruto) + tips"]
        S1 -->|"No (propietario asume)"| S1B["freenow_fixed =<br>bruto + tips"]
    end

    subgraph "Paso 2: Recaudacion"
        S2["recaudacion_total =<br>prima + freenow_fixed +<br>uber_t3 + adjustments"]
    end

    subgraph "Paso 3: Recaudacion Neta"
        S3["recaudacion_neta =<br>recaudacion_total - incidencias"]
    end

    subgraph "Paso 4: IVA"
        S4["iva = recaudacion_neta -<br>(recaudacion_neta / 1.1)"]
    end

    subgraph "Paso 5: Base Imponible"
        S5["base_imponible =<br>recaudacion_neta - iva"]
    end

    subgraph "Paso 6: Porcentaje Conductor"
        S6{"recaudacion_neta<br>>= threshold?"}
        S6 -->|Si| S6A["driver_pct = bonus_pct"]
        S6 -->|No| S6B["driver_pct = base_pct"]
    end

    subgraph "Paso 7: Parte Proporcional"
        S7["parte_proporcional =<br>base_imponible * driver_pct / 100"]
    end

    subgraph "Paso 8: FreeNow APP"
        S8{"freenow_commission<br>_driver_pct > 0?"}
        S8 -->|"No"| S8A["freenow_app =<br>app_bruto + app_tips +<br>adjustments"]
        S8 -->|"Si"| S8B["cash_commission =<br>cash_bruto * 12.5% * 1.21<br><br>freenow_app =<br>net(app_bruto) + app_tips +<br>adjustments - cash_commission"]
    end

    subgraph "Paso 9: Anticipado"
        S9["anticipado = recaudacion_neta<br>- tpv_visa - freenow_app<br>- uber_payment<br>- otros_gastos<br>- gasolina (si deducida)"]
    end

    subgraph "Paso 10: Cash"
        S10["cash = recaudacion_neta<br>- tpv_visa - freenow_app<br>- uber_payment"]
    end

    subgraph "Paso 11: Liquidacion"
        S11["liquidacion =<br>parte_proporcional - anticipado"]
    end

    IN1 --> S2
    IN2 --> S1
    IN3 --> S1
    S1A --> S2
    S1B --> S2
    IN4 --> S2
    IN13 --> S2
    S2 --> S3
    IN5 --> S3
    S3 --> S4
    S4 --> S5
    S3 --> S6
    S5 --> S7
    S6A --> S7
    S6B --> S7

    IN7 --> S8
    IN8 --> S8
    IN9 --> S8B
    IN13 --> S8

    S3 --> S9
    IN6 --> S9
    S8A --> S9
    S8B --> S9
    IN10 --> S9
    IN11 --> S9
    IN12 --> S9

    S3 --> S10
    IN6 --> S10
    S8A --> S10
    S8B --> S10
    IN10 --> S10

    S7 --> S11
    S9 --> S11
```

### 9.2 Formula paso a paso

#### Paso 1: FreeNow Fixed (neto o bruto)

Determina como entra FreeNow FIXED en la recaudacion dependiendo de quien asume la comision:

**Si el conductor asume la comision** (`freenow_commission_driver_pct > 0`):
```
freenow_fixed = calculate_freenow_net(bruto) + tips
```

**Si el propietario asume la comision** (`freenow_commission_driver_pct == 0`):
```
freenow_fixed = bruto + tips
```

Donde `calculate_freenow_net(bruto)` calcula:
```
comision = bruto * 12.5%
comision_con_iva = comision * 1.21
neto = bruto - comision_con_iva

Ejemplo: bruto = 100 EUR
  comision = 100 * 0.125 = 12.50
  comision_con_iva = 12.50 * 1.21 = 15.13
  neto = 100 - 15.13 = 84.88 EUR
```

Los ajustes de FreeNow (otros/incentivos) se suman despues:
```
freenow_fixed = freenow_fixed + freenow_adjustments
```

#### Paso 2: Recaudacion Total

Suma todos los ingresos del dia:
```
recaudacion_total = prima_amount + freenow_fixed + uber_t3_fixed
```

#### Paso 3: Recaudacion Neta

Resta las incidencias (tiquets nulos confirmados):
```
recaudacion_neta = recaudacion_total - incidents_amount
```

#### Paso 4: IVA (10%)

Extrae el IVA incluido en la recaudacion neta:
```
iva = recaudacion_neta - (recaudacion_neta / 1.1)

Ejemplo: recaudacion_neta = 200 EUR
  iva = 200 - (200 / 1.1) = 200 - 181.82 = 18.18 EUR
```

#### Paso 5: Base Imponible

Recaudacion sin IVA:
```
base_imponible = recaudacion_neta - iva

Ejemplo: 200 - 18.18 = 181.82 EUR
```

#### Paso 6: Porcentaje del Conductor

Sistema de comision escalonada:
```
Si recaudacion_neta >= commission_threshold:
    driver_pct = prima_bonus_pct  (ej: 45%)
Sino:
    driver_pct = prima_base_pct   (ej: 40%)

Si threshold == 0: siempre usa base_pct
```

#### Paso 7: Parte Proporcional

Lo que le corresponde al conductor de la recaudacion:
```
parte_proporcional = base_imponible * driver_pct / 100

Ejemplo: 181.82 * 40 / 100 = 72.73 EUR
```

#### Paso 8: FreeNow APP (pagos por transferencia)

Calcula lo que FreeNow ha pagado por transferencia:

**Si el propietario asume la comision** (`freenow_commission_driver_pct == 0`):
```
freenow_app = freenow_app_paid_bruto + freenow_app_tips + freenow_adjustments
```

**Si el conductor asume la comision** (`freenow_commission_driver_pct > 0`):
```
freenow_cash_commission = freenow_cash_bruto * 12.5% * 1.21

freenow_app = calculate_freenow_net(freenow_app_paid_bruto)
            + freenow_app_tips
            + freenow_adjustments
            - freenow_cash_commission
```

**Explicacion de la comision CASH**: FreeNow cobra su comision (12.5% + 21% IVA) sobre TODOS los viajes, incluidos los pagados en efectivo. Para los viajes CASH, FreeNow descuenta esta comision del pago por transferencia. Por eso se resta del `freenow_app`.

**Nota sobre fare_type**: `freenow_app_paid_bruto` incluye TODOS los viajes pagados por APP, tanto FIXED como METERED. No se filtra por `fare_type`.

#### Paso 9: Anticipado

Dinero que el conductor ya ha adelantado al propietario (lo que ha ingresado pero no es suyo):
```
anticipado = recaudacion_neta
           - tpv_visa_total       (cobrado por tarjeta/VISA)
           - freenow_app          (pagado por transferencia FreeNow)
           - uber_total_payment   (pagado por transferencia Uber)
           - other_expenses_total (gastos deducidos)
           - fuel_deduction       (gasolina, si fuel_deducted_from_driver)
```

#### Paso 10: Cash

Efectivo que tiene el conductor en mano:
```
cash = recaudacion_neta - tpv_visa_total - freenow_app - uber_total_payment
```

#### Paso 11: Liquidacion Final

Diferencia entre lo que le corresponde al conductor y lo que ya ha adelantado:
```
liquidacion = parte_proporcional - anticipado
```

| Resultado | Significado |
|-----------|------------|
| `liquidacion > 0` | El conductor ha adelantado mas de lo que le corresponde. El propietario le debe dinero. |
| `liquidacion < 0` | El conductor debe dinero al propietario (normalmente del efectivo recaudado). |
| `liquidacion == 0` | Estan en paz. |

### 9.3 Recopilacion de datos diarios

La funcion `_get_daily_data()` en `liquidacion.py` recopila todos los datos necesarios para un dia:

```mermaid
graph TD
    subgraph "Queries por dia"
        Q1["Prima trips<br>source=prima<br>driver_id/vehicle_id<br>Datetime naive"]
        Q2["FreeNow trips<br>source=freenow<br>driver_id/vehicle_id<br>Datetime tz-aware"]
        Q3["Incidencias<br>distance_km==0 AND<br>duration<0.5min<br>Excluye invalidadas"]
        Q4["UberDailySummary<br>por license_number<br>o vehicle_id"]
        Q5["TpvDailyTotal<br>por license_number<br>o vehicle_id"]
        Q6["FuelExpense<br>por vehicle_id"]
        Q7["OtherExpense<br>por driver_id"]
        Q8["FreenowAdjustment<br>por driver_id"]
    end

    Q1 --> AGG["Agregacion"]
    Q2 --> AGG
    Q3 --> AGG
    Q4 --> AGG
    Q5 --> AGG
    Q6 --> AGG
    Q7 --> AGG
    Q8 --> AGG

    AGG --> OUT["Dict con 13 campos:<br>prima_amount, freenow_fixed_bruto,<br>freenow_fixed_tips, uber_t3_fixed,<br>incidents_amount, tpv_visa_total,<br>freenow_app_paid_bruto, freenow_app_tips,<br>freenow_cash_bruto, uber_total_payment,<br>fuel_total, other_expenses_total,<br>freenow_adjustments"]
```

### 9.4 Manejo de zonas horarias

| Plataforma | Tipo de datetime | Zona horaria |
|-----------|-----------------|-------------|
| **Prima** | Naive (sin timezone) | Se asume hora local |
| **FreeNow** | Aware (con timezone) | Europe/Madrid |
| **Ventana diaria** | Prima: `datetime.combine(date, time.min)` | FreeNow: `datetime.combine(date, time.min, tzinfo=Europe/Madrid)` |

### 9.5 Ejemplo numerico completo

**Datos del dia:**
| Campo | Valor |
|-------|-------|
| prima_amount | 127.35 EUR |
| freenow_fixed_bruto | 70.20 EUR |
| freenow_fixed_tips | 5.00 EUR |
| uber_t3_fixed | 25.00 EUR |
| incidents_amount | 0.00 EUR |
| tpv_visa_total | 80.00 EUR |
| freenow_app_paid_bruto | 50.00 EUR |
| freenow_app_tips | 3.00 EUR |
| uber_total_payment | 60.00 EUR |
| fuel_total | 30.00 EUR |
| other_expenses_total | 0.00 EUR |
| freenow_adjustments | 10.00 EUR |

**Configuracion conductor:** base_pct=40%, bonus_pct=45%, threshold=300, freenow_commission_driver_pct=0, fuel_deducted=true

**Calculo:**

1. `freenow_fixed = 70.20 + 5.00 + 10.00 = 85.20` (propietario asume comision)
2. `recaudacion_total = 127.35 + 85.20 + 25.00 = 237.55`
3. `recaudacion_neta = 237.55 - 0.00 = 237.55`
4. `iva = 237.55 - (237.55 / 1.1) = 237.55 - 215.95 = 21.59`
5. `base_imponible = 237.55 - 21.59 = 215.95`
6. `driver_pct = 40%` (237.55 < 300 threshold)
7. `parte_proporcional = 215.95 * 40 / 100 = 86.38`
8. `freenow_app = 50.00 + 3.00 + 10.00 = 63.00` (propietario asume comision)
9. `anticipado = 237.55 - 80.00 - 63.00 - 60.00 - 0.00 - 30.00 = 4.55`
10. `cash = 237.55 - 80.00 - 63.00 - 60.00 = 34.55`
11. `liquidacion = 86.38 - 4.55 = 81.83` (propietario debe al conductor)

---

## 10. Dashboard de KPIs

El dashboard (`src/routes/dashboard.py`) muestra metricas mensuales comparativas para todos los conductores activos.

### 10.1 KPIs calculados

```mermaid
graph LR
    subgraph "Fuentes"
        PRIMA["Prima Trips"]
        FN["FreeNow Trips<br>(solo FIXED)"]
        UBER["UberDailySummary"]
        FUEL["FuelExpense"]
    end

    subgraph "KPIs de Ingresos"
        K1["prima_amount"]
        K2["freenow_t3<br>(net o bruto)"]
        K3["uber_t3"]
        K4["total_rec"]
        K5["total_rec_neta"]
    end

    subgraph "KPIs de Eficiencia"
        K6["km_occupied"]
        K7["km_free"]
        K8["eur_per_km"]
        K9["eur_per_viaje"]
        K10["promedio_diario"]
        K11["tasa_ocupacion"]
    end

    subgraph "KPIs de Plataforma"
        K12["pct_prima"]
        K13["pct_freenow"]
        K14["pct_uber"]
    end

    subgraph "KPIs de Combustible"
        K15["fuel_cost"]
        K16["fuel_liters"]
        K17["fuel_price_per_liter"]
        K18["fuel_pct"]
        K19["fuel_cost_per_km"]
    end

    PRIMA --> K1
    FN --> K2
    UBER --> K3
    K1 & K2 & K3 --> K4
    K1 & K2 & K3 --> K5
    PRIMA --> K6
    PRIMA --> K7
    K5 --> K8
    K5 --> K9
    K5 --> K10
    K6 & K7 --> K11
    K1 & K2 & K3 & K5 --> K12 & K13 & K14
    FUEL --> K15 & K16 & K17 & K18 & K19
```

### 10.2 Formulas de KPIs

| KPI | Formula |
|-----|---------|
| total_rec | prima + freenow_bruto + freenow_tips + uber_t3 |
| total_rec_neta | prima + freenow_net + freenow_tips + uber_t3 |
| dias | Dias unicos trabajados (union Prima + FreeNow + Uber) |
| viajes | prima_trips + freenow_trips (Uber no cuenta individualmente) |
| eur_per_km | total_rec_neta / total_km |
| eur_per_viaje | total_rec_neta / viajes |
| promedio_diario | total_rec_neta / dias |
| tasa_ocupacion | km_occupied / total_km * 100 |
| fuel_pct | fuel_cost / total_rec_neta * 100 |
| fuel_cost_per_km | fuel_cost / total_km |

---

## 11. Deteccion de Incidencias

### 11.1 Criterios de deteccion

Un viaje se marca como posible incidencia si cumple AMBAS condiciones:
- `distance_km == 0` (sin desplazamiento)
- `duration_minutes < 0.5` (menos de 30 segundos)

Esto indica un posible tiquet nulo: el taximetro se abrio y cerro sin realizar un viaje real.

### 11.2 Flujo de validacion de incidencias

```mermaid
stateDiagram-v2
    [*] --> Detectada: Import CSV/Scraper
    Detectada --> Pendiente: create_incident_validations()
    Pendiente --> Valida: Admin marca "Valido"
    Pendiente --> Invalida: Admin marca "Invalido"
    Valida --> [*]: Se descuenta en liquidacion
    Invalida --> [*]: Se ignora en liquidacion

    note right of Detectada
        distance_km == 0 AND
        duration_minutes < 0.5
    end note

    note right of Valida
        incidents_amount incluye
        el gross_amount del viaje
    end note

    note right of Invalida
        El trip_id se excluye
        de la suma de incidencias
    end note
```

### 11.3 Impacto en la liquidacion

Los viajes marcados como **validos** (incidencias confirmadas) se suman a `incidents_amount` y se restan de `recaudacion_total` para obtener `recaudacion_neta`. Los marcados como **invalidos** se excluyen del calculo.

---

## 12. Exportacion de Datos

### 12.1 Columnas del informe de liquidacion

Los informes Excel y PDF contienen 17 columnas identicas:

| # | Columna | Campo interno | Descripcion |
|---|---------|---------------|-------------|
| 1 | Fecha | date | Dia del calculo |
| 2 | Prima | prima_amount | Ingresos taximetro |
| 3 | Inc | incidents_amount | Incidencias descontadas |
| 4 | FreenowT3 | freenow_fixed | FreeNow FIXED neto/bruto + ajustes |
| 5 | Uber T3 | uber_t3_fixed | Uber T3 fijo |
| 6 | Rec. Neta | recaudacion_neta | Recaudacion neta |
| 7 | % | driver_pct | Porcentaje conductor |
| 8 | TPV | tpv_visa_total | Total pagos VISA/tarjeta |
| 9 | App FN | freenow_app | Pagos FreeNow por app |
| 10 | App Uber | uber_total_payment | Pagos Uber |
| 11 | Cash | cash | Efectivo en mano |
| 12 | IVA | iva | IVA 10% |
| 13 | Parte Prop. | parte_proporcional | Parte proporcional conductor |
| 14 | Gasolina | fuel_total | Gastos combustible |
| 15 | Otros | other_expenses_total | Otros gastos |
| 16 | Anticipado | anticipado | Dinero adelantado |
| 17 | Liquidacion | liquidacion | Resultado final |

### 12.2 Excel (openpyxl)

- **Formato**: XLSX con estilos (cabeceras azules, totales resaltados)
- **Nombre archivo**: `liquidacion_{conductor}_{fecha_inicio}_{fecha_fin}.xlsx`
- **Formato numeros**: `#,##0.00`
- **Fila totales**: Suma de todas las columnas con fondo azul claro

### 12.3 PDF (fpdf2)

- **Orientacion**: Apaisado (landscape) A4
- **Fuente**: Helvetica 6pt
- **Filas alternadas**: Gris claro / blanco
- **Cabecera**: Fondo azul (68, 114, 196), texto blanco
- **Nombre archivo**: `liquidacion_{conductor}_{fecha_inicio}_{fecha_fin}.pdf`

---

## 13. Autenticacion y Seguridad

### 13.1 Flujo de autenticacion

```mermaid
sequenceDiagram
    participant User as Usuario
    participant Browser as Navegador
    participant FastAPI as FastAPI
    participant DB as PostgreSQL

    User->>Browser: Acceder a /
    Browser->>FastAPI: GET /
    FastAPI->>FastAPI: Verificar cookie JWT
    FastAPI-->>Browser: Redirect /login (sin cookie)

    User->>Browser: Introducir email + password
    Browser->>FastAPI: POST /login (form)
    FastAPI->>FastAPI: Rate limit check (5/5min)
    FastAPI->>DB: Query Driver por email
    DB-->>FastAPI: Driver record
    FastAPI->>FastAPI: bcrypt.verify(password, hash)
    FastAPI->>FastAPI: Generar JWT (sub, role, name)
    FastAPI-->>Browser: Set-Cookie: access_token (httponly)
    Browser->>FastAPI: GET / (con cookie)
    FastAPI->>FastAPI: Decodificar JWT
    FastAPI-->>Browser: Dashboard HTML
```

### 13.2 Configuracion de seguridad

| Medida | Implementacion |
|--------|---------------|
| **Cookies** | httponly=True, secure=True (produccion), samesite=lax |
| **JWT** | HS256, expiracion 24 horas |
| **Rate limiting** | 5 intentos login / 5 min por IP; 60 requests/min general |
| **CSRF** | Middleware que verifica Origin/Referer en POST/PUT/DELETE |
| **XSS** | Jinja2 auto-escaping en templates |
| **Path traversal** | Validacion de filenames en visualizacion de archivos |
| **Passwords** | bcrypt hashing |

### 13.3 Roles y permisos

| Ruta | Admin/Owner | Conductor |
|------|------------|-----------|
| `/` (Dashboard) | Todos los conductores | Solo sus datos |
| `/liquidacion` | Acceso completo | Sin acceso |
| `/upload` | Acceso completo | Sin acceso |
| `/sync` | Acceso completo | Sin acceso |
| `/admin` | Acceso completo | Sin acceso |
| `/validacion` | Acceso completo | Sin acceso |
| `/trips` | Todos los viajes | Solo sus viajes |
| `/export` | Acceso completo | Solo sus datos |
| `/api/v1/*` | Acceso completo | Solo sus datos |

---

## 14. API REST v1

### 14.1 Autenticacion API

```
POST /api/v1/auth/login?email=...&password=...
→ {"access_token": "eyJ...", "token_type": "bearer"}

Headers: Authorization: Bearer <token>
```

### 14.2 Endpoints disponibles

| Metodo | Ruta | Descripcion | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/auth/login` | Obtener token Bearer | Publico |
| GET | `/api/v1/trips` | Listar viajes (paginado) | Bearer |
| GET | `/api/v1/trips/{id}` | Detalle de viaje | Bearer |
| GET | `/api/v1/drivers` | Listar conductores | Admin |
| GET | `/api/v1/drivers/{id}` | Detalle conductor | Bearer |
| GET | `/api/v1/vehicles` | Listar vehiculos | Admin |
| GET | `/api/v1/summary/daily` | Resumen diario | Bearer |
| GET | `/api/v1/summary/totals` | Totales del periodo | Bearer |
| GET | `/api/v1/sync/logs` | Logs de sincronizacion | Admin |
| POST | `/api/v1/sync/{source}` | Iniciar sincronizacion | Admin |
| GET | `/api/v1/validations` | Incidencias pendientes | Admin |
| POST | `/api/v1/validations/{id}/resolve` | Resolver incidencia | Admin |
| GET | `/api/v1/visa-payments` | Pagos VISA | Admin |
| GET | `/api/v1/fuel-expenses` | Gastos combustible | Admin |

### 14.3 Filtros comunes

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `driver_id` | string | Filtrar por conductor |
| `source` | string | Filtrar por plataforma (prima/freenow/uber) |
| `date_from` | date | Fecha inicio (YYYY-MM-DD) |
| `date_to` | date | Fecha fin (YYYY-MM-DD) |
| `page` | int | Pagina (default: 1) |
| `per_page` | int | Registros por pagina (default: 50) |

---

## 15. Sistema de Trabajos Asincronos

### 15.1 Arquitectura Arq + Redis

```mermaid
graph LR
    subgraph "FastAPI Process"
        ROUTE["Ruta /sync/*"]
        JOB_SVC["job_service.py<br>enqueue_sync()"]
    end

    subgraph "Redis"
        QUEUE["Cola Arq<br>(arq:queue)"]
    end

    subgraph "Worker Process"
        ARQ["Arq Worker"]
        TASK_FN["sync_freenow()"]
        TASK_PR["sync_prima()"]
        SCRAPER_FN["FreeNowScraper"]
        SCRAPER_PR["PrimaScraper"]
    end

    ROUTE -->|"1. Crear SyncLog"| JOB_SVC
    JOB_SVC -->|"2. Encolar"| QUEUE
    QUEUE -->|"3. Consumir"| ARQ
    ARQ --> TASK_FN
    ARQ --> TASK_PR
    TASK_FN --> SCRAPER_FN
    TASK_PR --> SCRAPER_PR
```

### 15.2 Ciclo de vida de un trabajo

```mermaid
stateDiagram-v2
    [*] --> Queued: enqueue_sync()
    Queued --> Running: Worker consume
    Running --> Success: Scraping + Import OK
    Running --> Error: Exception capturada
    Success --> [*]: SyncLog actualizado
    Error --> [*]: SyncLog con error_message

    note right of Running
        1. Lanzar Playwright
        2. Login en portal
        3. Descargar CSV
        4. Parsear e importar
        5. Detectar incidencias
    end note
```

### 15.3 Proteccion contra ejecucion doble

Antes de encolar un nuevo trabajo, el sistema verifica que no haya un SyncLog con `status="running"` para la misma plataforma. Si existe, redirige sin encolar.

---

## 16. Cumplimiento GDPR

### 16.1 Anonimizacion de datos GPS

- **Politica**: Datos GPS (coordenadas origen/destino) se anulan despues de 90 dias
- **Funcion**: `gdpr_service.anonymize_old_gps(session)`
- **Campos**: `origin_lat`, `origin_lng`, `dest_lat`, `dest_lng` → `NULL`

### 16.2 Purgado de tokens

- **Politica**: Tokens de plataforma expirados o revocados se eliminan
- **Funcion**: `gdpr_service.purge_expired_tokens(session)`
- **Criterios**: `expires_at < now` OR `is_valid == False` OR `revoked_at IS NOT NULL`

### 16.3 Solicitudes de acceso (DSR)

- **Modelo**: `DsrRequest` para rastrear solicitudes de acceso a datos personales
- **Tipos**: access (consulta), deletion (eliminacion), rectification (correccion)

---

## 17. Despliegue y Operaciones

### 17.1 Arquitectura de despliegue

```mermaid
graph TB
    subgraph "GitHub"
        REPO["Repositorio TAXI2"]
        GHA["GitHub Actions<br>CI/CD Pipeline"]
        GHCR["GitHub Container<br>Registry (GHCR)"]
    end

    subgraph "Servidor VPS (OVH)"
        NGINX["Nginx<br>Reverse Proxy"]
        subgraph "Docker Compose"
            API["taxi-api<br>:8000"]
            WORKER["taxi-worker"]
            REDIS["taxi-redis<br>:6379"]
            DB["taxi-db<br>:5432"]
        end
    end

    REPO -->|"push"| GHA
    GHA -->|"build & push"| GHCR
    GHA -->|"SSH deploy"| API
    GHCR -->|"pull image"| API
    NGINX -->|"proxy_pass"| API
```

### 17.2 Pipeline CI/CD

```mermaid
graph LR
    A["Push a main"] --> B["GitHub Actions"]
    B --> C["Run tests<br>(pytest)"]
    C --> D["Build Docker image"]
    D --> E["Push to GHCR"]
    E --> F["SSH to server"]
    F --> G["docker pull"]
    G --> H["docker compose<br>up -d"]
```

### 17.3 Variables de entorno requeridas

| Variable | Descripcion |
|----------|-------------|
| `DATABASE_URL` | URL PostgreSQL |
| `SECRET_KEY` | Clave para firma JWT |
| `REDIS_URL` | URL Redis |
| `FREENOW_EMAIL` / `FREENOW_PASSWORD` | Credenciales cuenta 1 |
| `FREENOW_2_EMAIL` / `FREENOW_2_PASSWORD` | Credenciales cuenta 2 |
| `PRIMA_EMAIL` / `PRIMA_PASSWORD` | Credenciales Prima |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | Config SMTP |
| `ALERT_EMAIL_TO` | Email para alertas |
| `ROOT_PATH` | Path base (para reverse proxy) |

### 17.4 Comandos operativos

```bash
# Levantar servicios
docker compose up -d

# Ver logs
docker logs taxi-api -f
docker logs taxi-worker -f

# Ejecutar migraciones
docker exec taxi-api alembic upgrade head

# Acceder a la base de datos
docker exec -it taxi-db psql -U taxi -d taxi_api

# Reconstruir imagen
docker compose build --no-cache taxi-api
docker compose up -d
```

---

## 18. Estructura de Archivos del Proyecto

```
TAXI2/
├── src/
│   ├── main.py                      # FastAPI app, routers, middleware
│   ├── config.py                    # Settings (env vars, credenciales)
│   ├── database.py                  # SQLAlchemy engine + session
│   ├── template_config.py           # Jinja2 templates config
│   ├── models/
│   │   ├── __init__.py              # Exporta todos los modelos
│   │   ├── owner.py                 # Owner model
│   │   ├── driver.py                # Driver model (comisiones)
│   │   ├── vehicle.py               # Vehicle model
│   │   ├── trip.py                  # Trip model (multi-plataforma)
│   │   ├── shift.py                 # Shift model
│   │   ├── fuel_expense.py          # FuelExpense model
│   │   ├── other_expense.py         # OtherExpense model
│   │   ├── freenow_adjustment.py    # FreenowAdjustment model
│   │   ├── tpv_daily_total.py       # TpvDailyTotal model
│   │   ├── uber_daily_summary.py    # UberDailySummary model
│   │   ├── visa_payment.py          # VisaPayment model
│   │   ├── pending_validation.py    # PendingValidation model
│   │   ├── sync_log.py              # SyncLog model
│   │   ├── freenow_import.py        # FreeNowImport model
│   │   ├── daily_summary.py         # DailySummary model
│   │   ├── platform_token.py        # PlatformToken model
│   │   └── dsr_request.py           # DsrRequest model (GDPR)
│   ├── routes/
│   │   ├── auth.py                  # Login, logout, JWT
│   │   ├── dashboard.py             # KPI dashboard mensual
│   │   ├── liquidacion.py           # Calculo liquidacion
│   │   ├── upload.py                # Carga CSV/XLSX
│   │   ├── sync.py                  # Sincronizacion scrapers
│   │   ├── trips.py                 # Listado viajes
│   │   ├── admin.py                 # Gestion conductores/vehiculos
│   │   ├── validation.py            # Validacion incidencias
│   │   ├── export.py                # Export CSV
│   │   ├── summary.py               # Resumen diario
│   │   └── api_v1.py                # API REST v1
│   ├── services/
│   │   ├── settlement_calculator.py # Motor de liquidacion
│   │   ├── incident_detector.py     # Deteccion incidencias
│   │   ├── excel_exporter.py        # Export Excel
│   │   ├── pdf_exporter.py          # Export PDF
│   │   ├── job_service.py           # Encolado Arq
│   │   ├── auth_service.py          # JWT + bcrypt
│   │   ├── trip_service.py          # Analytics viajes
│   │   ├── trip_matcher.py          # Match Prima↔FreeNow/Uber
│   │   ├── csv_validator.py         # Validacion esquema CSV
│   │   ├── email_service.py         # Notificaciones SMTP
│   │   ├── gap_detector.py          # Deteccion gaps sync
│   │   ├── gdpr_service.py          # Anonimizacion GDPR
│   │   ├── token_encryption.py      # Cifrado tokens
│   │   └── summary_service.py       # Servicio resumenes
│   ├── workers/
│   │   ├── tasks.py                 # Jobs Arq (sync_freenow, sync_prima)
│   │   └── settings.py              # Config Redis worker
│   ├── templates/                   # Templates Jinja2 (14 archivos)
│   └── static/                      # Archivos estaticos
├── scripts/
│   └── parsers/
│       ├── freenow_parser.py        # Parser CSV FreeNow
│       ├── prima_parser.py          # Parser CSV Prima
│       ├── uber_parser.py           # Parser CSV Uber
│       ├── lacaixa_parser.py        # Parser XLSX La Caixa
│       ├── petroprix_parser.py      # Parser CSV Petroprix
│       └── repsol_parser.py         # Parser XLSX Repsol
├── scrapers/
│   ├── base_scraper.py              # Base class Playwright
│   ├── freenow_scraper.py           # Scraper portal FreeNow
│   ├── prima_scraper.py             # Scraper portal Prima
│   └── uber_scraper.py              # Scraper portal Uber
├── migrations/
│   └── versions/                    # Migraciones Alembic
├── tests/
│   └── unit/                        # Tests unitarios
├── docker-compose.yml               # Orquestacion contenedores
├── Dockerfile.prod                  # Imagen produccion
└── alembic.ini                      # Config Alembic
```
