# TAXI API - Estado Completo del Proyecto

**Ultima actualizacion:** 2026-02-08
**Para:** Contexto completo al iniciar cualquier sesion de trabajo

---

## 1. Infraestructura

### Repositorio
- **GitHub:** github.com/ivantintore/TAXI2
- **Branch:** main
- **Ultimo commit:** `c4b78fa` docs: update PROJECT_STATUS.md

### Servidor de produccion (VPS)
- **IP:** 51.77.144.212
- **SSH:** `ssh ubuntu@51.77.144.212`
- **Codigo:** `/opt/taxi-api/repo`
- **URL publica:** `https://keonycs.com/tools3/taxi/`
- **Reverse proxy:** Caddy (container `dashboard-caddy`)
- **Dashboard:** Taxi API aparece como tarjeta en `https://keonycs.com/tools3/`

### Docker Compose (produccion)
4 containers en `docker-compose.prod.yml`:

| Container | Imagen | Puerto | Status |
|-----------|--------|--------|--------|
| taxi-db | postgres:15-alpine | interno | healthy |
| taxi-redis | redis:7-alpine | interno | healthy |
| taxi-api | ghcr.io/ivantintore/taxi-api:latest | 127.0.0.1:8010->8000 | healthy |
| taxi-worker | ghcr.io/ivantintore/taxi-api:latest (cmd: arq) | ninguno | running |

### Volumenes persistentes
- `taxi-api_taxi_pg_data` - PostgreSQL data
- `taxi-api_taxi_imports` - CSVs importados

---

## 2. Produccion - FUNCIONANDO

### URL: `https://keonycs.com/tools3/taxi/` - HTTP 200 OK

### Caddy config (en `/etc/caddy/Caddyfile` dentro de `dashboard-caddy`):
```
# Auth PROPIA (no usa Auth V3 / forward_auth)
handle /tools3/taxi {
    redir /tools3/taxi/ permanent
}
handle /tools3/taxi/* {
    uri strip_prefix /tools3/taxi
    reverse_proxy taxi-api:8000
}
```

### Autenticacion
- **NO usa Auth0 ni Auth V3** (el bloque Caddy no tiene `forward_auth`)
- Sistema propio: email + password → JWT cookie (HttpOnly, Secure, SameSite=lax)
- Passwords hasheados con bcrypt
- JWT expira en 24h (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Rate limiting en login: 5 intentos por IP cada 5 minutos
- API REST acepta JWT como Bearer token en header `Authorization`
- **No hay usuarios creados todavia** - hay que insertar el primero en la DB manualmente

---

## 3. CI/CD

### GitHub Actions (`.github/workflows/deploy.yml`)
Pipeline: Test (pytest) → Build (GHCR) → Deploy (SSH)

### Problema conocido
- El pipeline usa `docker compose` (v2) pero el VPS tiene `docker-compose` v1.29.2
- Deploy automatico puede fallar

### Deploy manual (lo que funciona)
```bash
ssh ubuntu@51.77.144.212 "cd /opt/taxi-api/repo && sudo git pull origin main && sudo docker build -t ghcr.io/ivantintore/taxi-api:latest -f Dockerfile.prod . && sudo docker stop taxi-worker taxi-api || true && sudo docker rm taxi-worker taxi-api || true && sudo docker-compose -f docker-compose.prod.yml up -d"
```

**IMPORTANTE:** No usar `--force-recreate` — docker-compose v1.29.2 tiene un bug (`ContainerConfig` KeyError). Siempre hacer stop/rm/up.

---

## 4. Stack tecnologico

| Componente | Tecnologia |
|-----------|------------|
| Backend | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Templates | Jinja2 3.1 |
| DB | PostgreSQL 15 |
| Queue | Redis 7 + Arq 0.26 |
| Scrapers | Playwright 1.49 (Chromium headless, sync API via `asyncio.to_thread()`) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Migrations | Alembic 1.14 |
| Email | aiosmtplib 3.0 |
| Data | pandas 2.2, openpyxl 3.1, pdfplumber 0.11, fpdf2 2.8 |
| Rate limiting | slowapi 0.1.9 |
| Python | 3.11 (Docker), 3.14 (local dev) |

---

## 5. Modelos de datos (15 modelos)

### Entidades principales

| Modelo | Archivo | Campos clave |
|--------|---------|-------------|
| **Owner** | src/models/owner.py | id (UUID), name, tax_id, email, phone |
| **Driver** | src/models/driver.py | id (UUID), name, email, password_hash, is_owner, owner_id, license_number, commission_base_pct (40%), commission_bonus_pct (45%), commission_threshold (300€), uber_driver_id, freenow_driver_id |
| **Vehicle** | src/models/vehicle.py | id (UUID), plate, license_number, model, brand, owner_id, taximeter_id, uber_vehicle_id, freenow_vehicle_id |

### Datos de viajes

| Modelo | Archivo | Campos clave |
|--------|---------|-------------|
| **Trip** | src/models/trip.py | id (UUID), source (uber/freenow/prima), external_id, driver_id, vehicle_id, started_at, ended_at, distance_km, gross_amount, commission, payout_amount, payment_method, linked_trip_id (self FK para cross-match), raw_data (JSON) |
| **Shift** | src/models/shift.py | id (UUID), driver_id, vehicle_id, source, started_at, ended_at, km_free, km_occupied, total_earnings |
| **DailySummary** | src/models/daily_summary.py | id (UUID), date, driver_id, vehicle_id, trips por plataforma, total_km, total_gross, euro_per_km. Unique(date, driver_id, vehicle_id) |

### Pagos y gastos

| Modelo | Archivo | Campos clave |
|--------|---------|-------------|
| **VisaPayment** | src/models/visa_payment.py | id (UUID), date, time, amount, card_last4, trip_id (FK, matched), vehicle_id, tip_amount |
| **FuelExpense** | src/models/fuel_expense.py | id (UUID), date, vehicle_id, driver_id, liters, amount, provider (petroprix/repsol) |
| **OtherExpense** | src/models/other_expense.py | id (UUID), date, driver_id, amount, category (parking/lavado/peaje/otro) |

### Sistema

| Modelo | Archivo | Campos clave |
|--------|---------|-------------|
| **SyncLog** | src/models/sync_log.py | id (UUID), source, status, records_found/created/updated/skipped, error_message |
| **PendingValidation** | src/models/pending_validation.py | id (UUID), trip_id, validation_type (incident/visa_no_match/fuel_no_match), status (pending/valid/invalid) |
| **PlatformToken** | src/models/platform_token.py | id (UUID), driver_id, platform, access_token_encrypted, refresh_token_encrypted, expires_at |
| **FreeNowImport** | src/models/freenow_import.py | id (UUID), filename, file_hash, status, records_imported |
| **DsrRequest** | src/models/dsr_request.py | id (UUID), request_type, subject_type, status (GDPR) |

---

## 6. Parsers (6 archivos en scripts/parsers/)

| Parser | Archivo | Formato entrada | Salida |
|--------|---------|----------------|--------|
| **Uber** | uber_parser.py | CSV (coma) | Trips con source="uber" |
| **FreeNow** | freenow_parser.py | CSV (coma, ISO 8601) | Trips + `_driver_name` + `_plate` para auto-match |
| **Prima** | prima_parser.py | CSV (punto y coma, decimales europeos) | Trips + `_license` para match. Map hardcodeado de conductores (DriverNum → nombre) |
| **La Caixa** | lacaixa_parser.py | Excel (.xlsx) | VisaPayments con date, time, amount, card_last4, terminal_id |
| **Petroprix** | petroprix_parser.py | CSV (decimales europeos) | FuelExpenses + `_plate` para match vehiculo |
| **Repsol** | repsol_parser.py | PDF (pdfplumber OCR) | FuelExpenses + `_plate` + `_driver` para match |

---

## 7. Scrapers (scrapers/)

| Scraper | Archivo | Portal | Metodo | Estado |
|---------|---------|--------|--------|--------|
| **FreeNow** | freenow_scraper.py | portal.free-now.com | Login → booking-history → date range → CSV ZIP download | Funciona (24 trips verificados) |
| **Prima** | prima_scraper.py | prima.taxitronic.com | Login → ConsultaTurnos → date range → Exportar CSV | Funciona (64 trips verificados) |
| **Uber** | uber_scraper.py | — | Skeleton, solo upload manual | No implementado |

- Base class: `base_scraper.py` (Playwright boilerplate)
- Discovery tools: `freenow_discover.py`, `uber_discover.py` (exploracion de portales)

---

## 8. Servicios de negocio (15 archivos en src/services/)

| Servicio | Archivo | Funcion |
|----------|---------|---------|
| **auth_service** | auth_service.py | JWT create/decode, bcrypt hash/verify |
| **trip_service** | trip_service.py | Dashboard earnings, analytics avanzado (EUR/km, EUR/hora, comparativa drivers), lista paginada |
| **trip_matcher** | trip_matcher.py | Cross-match Prima ↔ FreeNow/Uber (ventana ±65min, amount≈0 en Prima) |
| **visa_matcher** | visa_matcher.py | Match VISA pagos → trips (±10min desde trip end), calcula propina |
| **incident_detector** | incident_detector.py | Detecta tickets nulos (0km + <30s) → crea PendingValidation |
| **settlement_calculator** | settlement_calculator.py | Liquidacion completa: FreeNow bruto→neto (÷1.125×1.21), IVA 10%, comisiones base/bonus, cash/deuda |
| **excel_exporter** | excel_exporter.py | Export liquidacion a XLSX formateado |
| **pdf_exporter** | pdf_exporter.py | Export liquidacion a PDF landscape (fpdf2) |
| **job_service** | job_service.py | Encola jobs en Redis/Arq |
| **email_service** | email_service.py | Envio email via aiosmtplib, notifica incidencias/VISA pendientes |
| **csv_validator** | csv_validator.py | Valida columnas requeridas por plataforma antes de parsear |
| **gdpr_service** | gdpr_service.py | Anonimiza GPS >90 dias (bulk UPDATE), purga tokens expirados |
| **token_encryption** | token_encryption.py | Fernet encrypt/decrypt, key derivada de SECRET_KEY via SHA-256 |
| **gap_detector** | gap_detector.py | Alerta si plataforma sin sync exitoso >3 dias |
| **summary_service** | summary_service.py | Placeholder (logica en routes/summary.py) |

---

## 9. Paginas web (UI - src/templates/)

| Pagina | Ruta | Funcionalidad |
|--------|------|--------------|
| **Login** | /login | Email + password |
| **Dashboard** | / | Earnings hoy/semana/mes + grafico diario (Chart.js) + trips recientes |
| **Viajes** | /trips | Lista paginada (50/pag) + filtros (fecha, driver, source, payment) + entrada manual Uber |
| **Sync** | /sync | Trigger FreeNow/Prima scrapers + cross-match + file browser + sync logs |
| **Upload** | /upload | Subir CSV/XLSX/PDF con auto-detect plataforma. Soporta: Uber, FreeNow, Prima, La Caixa, Petroprix, Repsol |
| **Admin** | /admin | CRUD drivers/vehicles/owners + comisiones |
| **Validacion** | /validacion | 3 tabs: incidencias, VISA sin match, combustible sin match. Resolver como valido/invalido |
| **Liquidacion** | /liquidacion | Calculo liquidacion por conductor + tabla diaria + export Excel/PDF |
| **Summary** | /summary | Agregaciones diarias con filtros fecha/driver/vehicle + totales |
| **Export** | /export | Descargar viajes o resumen diario en CSV o Excel |

Base template: `base.html` (Bootstrap 5 + Chart.js)

---

## 10. REST API (/api/v1/)

Autenticacion: Bearer token (JWT). Rate limiting: 60/min default.

| Metodo | Endpoint | Descripcion | Restriccion |
|--------|----------|-------------|-------------|
| POST | /api/v1/auth/login | Obtener token | 5/min |
| GET | /api/v1/trips | Listar viajes (paginado, filtros) | — |
| GET | /api/v1/trips/{id} | Detalle viaje | — |
| GET | /api/v1/drivers | Listar conductores | admin |
| GET | /api/v1/drivers/{id} | Detalle conductor | admin |
| GET | /api/v1/vehicles | Listar vehiculos | admin |
| GET | /api/v1/summary/daily | Agregaciones diarias | — |
| GET | /api/v1/summary/totals | Totales del periodo | — |
| GET | /api/v1/sync/logs | Logs de sync | admin |
| POST | /api/v1/sync/{source} | Trigger sync | admin, 2/min |
| GET | /api/v1/validations | Validaciones pendientes | admin |
| POST | /api/v1/validations/{id}/resolve | Resolver validacion | admin |
| GET | /api/v1/visa-payments | Pagos VISA | admin |
| GET | /api/v1/fuel-expenses | Gastos combustible | admin |

---

## 11. Workers (Arq cron jobs)

| Job | Funcion | Horario (UTC) |
|-----|---------|---------------|
| **sync_freenow** | Scraper FreeNow (ultimo dia) | 02:00 |
| **sync_prima** | Scraper Prima (ultimo dia) | 02:05 |
| **gdpr_cleanup** | Anonimizar GPS >90d + purgar tokens | 03:00 |
| **gap_check** | Alertar si >3 dias sin sync + email | 08:00 |

Config: max_jobs=2, job_timeout=600s, keep_result=3600s

---

## 12. Tests

19 archivos en `tests/unit/`:
- Modelos: driver, visa_payment, fuel_expense, other_expense, pending_validation, models (general)
- Parsers: uber, freenow, prima, lacaixa, petroprix, repsol
- Servicios: auth, config, database, email, incident_detector, visa_matcher, settlement_calculator

---

## 13. Bugs conocidos

| Bug | Estado | Workaround |
|-----|--------|------------|
| docker-compose v1 `ContainerConfig` KeyError | Conocido | Usar stop/rm/up, nunca --force-recreate |
| Prima conductor codes hardcodeados | Conocido | Map en prima_parser.py — actualizar si cambian conductores |
| CI/CD usa docker compose v2 vs VPS v1 | Conocido | Deploy manual via SSH |

Bugs ya resueltos: 502 produccion, Playwright async loop, entrypoint.sh CMD override.

---

## 14. Estructura de archivos

```
TAXI_API/
  src/
    main.py                          # FastAPI app + middleware CSRF + routers + rate limiting
    config.py                        # Pydantic Settings (env vars)
    database.py                      # SQLAlchemy engine + get_session()
    template_config.py               # Jinja2 config + root_path
    models/                          # 15 SQLAlchemy models
      owner.py, driver.py, vehicle.py, trip.py, shift.py,
      daily_summary.py, visa_payment.py, fuel_expense.py,
      other_expense.py, sync_log.py, pending_validation.py,
      platform_token.py, freenow_import.py, dsr_request.py
    routes/                          # 11 route files
      auth.py, dashboard.py, trips.py, admin.py, upload.py,
      sync.py, summary.py, export.py, liquidacion.py,
      validation.py, api_v1.py
    services/                        # 15 service files
      auth_service.py, trip_service.py, trip_matcher.py,
      visa_matcher.py, incident_detector.py, settlement_calculator.py,
      excel_exporter.py, pdf_exporter.py, job_service.py,
      email_service.py, csv_validator.py, gdpr_service.py,
      token_encryption.py, gap_detector.py, summary_service.py
    workers/
      settings.py                    # Arq WorkerSettings + cron schedule
      tasks.py                       # 6 task functions (2 on-demand + 4 scheduled)
    templates/                       # 14 Jinja2 HTML templates
    static/                          # style.css + favicon.svg
  scrapers/
    base_scraper.py                  # Playwright base class
    freenow_scraper.py               # FreeNow portal scraper
    prima_scraper.py                 # Prima/Taxitronic scraper
    uber_scraper.py                  # Skeleton (no scraper real)
    freenow_discover.py              # Dev: explorar portal FreeNow
    uber_discover.py                 # Dev: explorar portal Uber
  scripts/parsers/                   # 6 parsers (CSV, XLSX, PDF)
  tests/unit/                        # 19 unit tests
  migrations/                        # Alembic migrations
  docs/plans/                        # Design docs
  docker-compose.yml                 # Dev
  docker-compose.prod.yml            # Prod (4 services)
  Dockerfile.prod                    # Python 3.11 + Playwright + Chromium
  entrypoint.sh                      # alembic upgrade head → uvicorn (o CMD custom)
  requirements.txt                   # 17 dependencias
  .github/workflows/deploy.yml       # CI/CD pipeline
  .env.example                       # Template variables de entorno
  PROJECT_STATUS.md                  # Este archivo
```

---

## 15. Variables de entorno (.env)

```
# Base de datos
DB_PASSWORD=<password-postgres>
DATABASE_URL=postgresql://taxi:<password>@taxi-db:5432/taxi_api

# Redis
REDIS_URL=redis://taxi-redis:6379

# Auth
SECRET_KEY=<random-string-32-chars>
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Credenciales scrapers
FREENOW_EMAIL=<email>
FREENOW_PASSWORD=<password>
PRIMA_USER=<usuario>
PRIMA_PASSWORD=<password>

# Email (opcional)
SMTP_HOST=<smtp-server>
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<password>
ALERT_EMAIL_TO=<admin-email>

# Reverse proxy
ROOT_PATH=/tools3/taxi
ENVIRONMENT=production
```

---

## 16. Historial de commits

```
c4b78fa docs: update PROJECT_STATUS.md - mark low priority tasks #14-#17 as completed
8ed6b99 feat: implement low priority tasks (#14-#17)
fe3513b docs: update PROJECT_STATUS.md - mark medium priority tasks #9-#13 as completed
c0d20e5 feat: implement medium priority tasks (#9-#13)
84c8bb6 docs: update PROJECT_STATUS.md - mark tasks #1-#8 as completed
72ef148 feat: implement pending features (tasks #3-#8 from PROJECT_STATUS)
b5f2104 fix: connect taxi-api to Caddy network + fix CI/CD for docker-compose v1
f69786e docs: add comprehensive project status document
20c20ec chore: gitignore data files (CSVs, Excel, PDFs, screenshots, imports)
eaa1c8c fix: run Playwright scrapers in thread within async Arq tasks
f0eb7c9 fix: entrypoint.sh now respects custom commands for worker container
f090392 chore: add FreeNow and Uber discovery scrapers
f5a754b fix: use existing external volumes in production
90b1c01 feat: replace threading with Arq job queue for scrapers
8e353cb feat(export): add Excel export for settlement
9a24a7e feat(ui): add settlement page with Excel-style table
c2efd8e feat(ui): add validation queue page
a2002a8 feat(admin): add commission configuration fields to driver edit
9e94416 feat(services): add settlement calculation service
919c346 feat(services): add VISA payment matching service
29b1dcc feat(services): add incident detection service
```

---

## 17. Logica de negocio clave

### Cross-match Prima ↔ FreeNow/Uber
- Prima registra TODOS los viajes (taximetro fisico), pero los de app tienen `amount≈0`
- FreeNow/Uber registran solo sus viajes con el importe real
- `trip_matcher.py` vincula Prima trip (amount=0) con el trip de app mas cercano en tiempo (±65min)
- El `linked_trip_id` de Prima apunta al trip de FreeNow/Uber

### Liquidacion (settlement)
- FreeNow bruto → neto: `bruto / 1.125 * 1.21` (quitar comision FreeNow, anadir IVA)
- IVA: 10% del total
- Comision conductor: base 40%, sube a 45% si supera threshold (300€)
- Cash vs app: Prima street trips = cash, app trips = liquidados por plataforma
- Resultado: lo que el conductor debe al propietario (o viceversa)

### VISA matching
- La Caixa XLSX tiene pagos VISA con hora exacta
- Match por proximidad temporal: ±10 minutos desde el fin del viaje
- Propina = importe VISA - importe viaje

---

## 18. Posibles mejoras futuras

- [ ] Scraper real de Uber (ahora es solo upload manual)
- [ ] Multi-owner support completo (ahora hay modelo Owner pero la UI asume un solo owner)
- [ ] Dashboard responsive / PWA para movil
- [ ] Integracion con contabilidad (facturacion electronica)
- [ ] Alertas push (Telegram/WhatsApp) ademas de email
- [ ] Backup automatico de PostgreSQL
- [ ] Migrar VPS de docker-compose v1 a v2
- [ ] Crear usuario admin inicial automaticamente (ahora hay que hacerlo manual en DB)
