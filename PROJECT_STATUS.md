# TAXI API - Estado del Proyecto

**Fecha:** 2026-02-08
**Para:** Contexto completo al iniciar cualquier sesion de trabajo

---

## 1. Infraestructura

### Repositorio
- **GitHub:** github.com/ivantintore/TAXI2
- **Branch:** main
- **Ultimo commit:** `20c20ec` chore: gitignore data files

### Servidor de produccion (VPS)
- **IP:** 51.77.144.212
- **SSH:** `ssh ubuntu@51.77.144.212`
- **Codigo:** `/opt/taxi-api/repo`
- **URL publica:** `https://keonycs.com/tools3/taxi/`
- **Reverse proxy:** Caddy (container `dashboard-caddy`)

### Docker Compose (produccion)
4 containers definidos en `docker-compose.prod.yml`:

| Container | Imagen | Puerto | Status |
|-----------|--------|--------|--------|
| taxi-db | postgres:15-alpine | interno | healthy |
| taxi-redis | redis:7-alpine | interno | healthy |
| taxi-api | ghcr.io/ivantintore/taxi-api:latest | 127.0.0.1:8010->8000 | healthy |
| taxi-worker | ghcr.io/ivantintore/taxi-api:latest (cmd: arq) | ninguno | running |

### Volumenes externos (datos persistentes)
- `taxi-api_taxi_pg_data` - PostgreSQL data
- `taxi-api_taxi_imports` - CSVs importados

---

## 2. BUG ACTIVO: 502 en produccion

### Sintoma
`https://keonycs.com/tools3/taxi/` devuelve HTTP 502 Bad Gateway.

### Causa raiz
Caddy (`dashboard-caddy`) y `taxi-api` estan en **redes Docker diferentes**:
- Caddy esta en: `dashboard_backend`, `dashboard_frontend`
- taxi-api esta en: `repo_default`

Caddy no puede resolver `taxi-api:8000` porque no comparten red.

### Configuracion actual de Caddy (en `/etc/caddy/Caddyfile` dentro del container `dashboard-caddy`):
```
handle /tools3/taxi {
    redir /tools3/taxi/ permanent
}
handle /tools3/taxi/* {
    uri strip_prefix /tools3/taxi
    reverse_proxy taxi-api:8000
}
```

### Nota sobre ROOT_PATH
- Caddy hace `uri strip_prefix /tools3/taxi` (quita el prefijo antes de enviar a FastAPI)
- FastAPI tiene `ROOT_PATH=/tools3/taxi` (genera URLs con el prefijo)
- El design doc original decia usar `handle` sin strip, pero en la practica se implemento con strip
- Esto puede causar conflictos: FastAPI genera links como `/tools3/taxi/login` pero recibe requests como `/login`

### Solucion necesaria
1. Conectar `taxi-api` a la red de Caddy: `docker network connect dashboard_backend taxi-api`
2. O bien: anadir `external: true` + `networks: dashboard_backend` en docker-compose.prod.yml
3. Verificar que la combinacion strip_prefix + ROOT_PATH funcione correctamente
4. Si no funciona: quitar strip_prefix en Caddy Y quitar ROOT_PATH en docker-compose, o viceversa

### Verificacion local (el API responde internamente)
```bash
ssh ubuntu@51.77.144.212 "curl -s http://localhost:8010/health"
# {"status":"healthy","version":"1.0.0","app":"TAXI API","root_path":"/tools3/taxi"}
```

---

## 3. CI/CD

### GitHub Actions (`.github/workflows/deploy.yml`)
Pipeline: Test -> Build (GHCR) -> Deploy (SSH)

### Problema conocido
- El pipeline usa `docker compose` (v2) pero el VPS tiene `docker-compose` v1.29.2
- El deploy step puede fallar por esta diferencia
- Hoy se hizo deploy manual: git pull + docker build + stop/rm/up

### Deploy manual (lo que funciona)
```bash
ssh ubuntu@51.77.144.212
cd /opt/taxi-api/repo
sudo git pull origin main
sudo docker build -t ghcr.io/ivantintore/taxi-api:latest -f Dockerfile.prod .
sudo docker stop taxi-worker taxi-api
sudo docker rm taxi-worker taxi-api
sudo docker-compose -f docker-compose.prod.yml up -d
```

**IMPORTANTE:** No usar `--force-recreate` - docker-compose v1.29.2 tiene un bug (`ContainerConfig` KeyError). Siempre hacer stop/rm/up.

---

## 4. Stack tecnologico

- **Backend:** FastAPI + SQLAlchemy + Jinja2 templates
- **DB:** PostgreSQL 15
- **Queue:** Redis + Arq (job queue asincrono)
- **Scrapers:** Playwright (Chromium headless) - sync API ejecutado via `asyncio.to_thread()`
- **Python:** 3.11 (en Docker), 3.14 (local dev)
- **Auth:** JWT en cookies, bcrypt para passwords
- **Migrations:** Alembic

---

## 5. Funcionalidades COMPLETADAS

### Modelos de datos (todos implementados)
Owner, Driver (con comisiones), Vehicle, Trip, Shift, SyncLog, FreeNowImport, DailySummary, PlatformToken, PendingValidation, VisaPayment, FuelExpense, OtherExpense

### Parsers (6 de 6)
| Parser | Archivo | Formato |
|--------|---------|---------|
| Uber | scripts/parsers/uber_parser.py | CSV de Uber |
| FreeNow | scripts/parsers/freenow_parser.py | CSV de FreeNow portal |
| Prima | scripts/parsers/prima_parser.py | CSV de Prima/Taxitronic |
| La Caixa | scripts/parsers/lacaixa_parser.py | XLSX de La Caixa (pagos VISA) |
| Petroprix | scripts/parsers/petroprix_parser.py | CSV de Petroprix (combustible) |
| Repsol | scripts/parsers/repsol_parser.py | PDF de Repsol/Solred (combustible) |

### Scrapers automaticos (via Arq job queue)
| Scraper | Archivo | Estado | Verificado |
|---------|---------|--------|------------|
| FreeNow | scrapers/freenow_scraper.py | Funciona | 2026-02-08 (24 trips importados) |
| Prima | scrapers/prima_scraper.py | Funciona | 2026-02-08 (64 trips importados) |
| Uber | scrapers/uber_scraper.py | Skeleton | No tiene scraper real, solo manual |

### Servicios de negocio
| Servicio | Archivo | Funcion |
|----------|---------|---------|
| Settlement calculator | src/services/settlement_calculator.py | Calculo completo de liquidacion |
| Incident detector | src/services/incident_detector.py | Detecta tickets nulos (0km + <30s) |
| VISA matcher | src/services/visa_matcher.py | Empareja pagos VISA con viajes (+/-10min) |
| Trip matcher | src/services/trip_matcher.py | Cross-match Prima <-> FreeNow/Uber |
| Excel exporter | src/services/excel_exporter.py | Export liquidacion a Excel |
| Job service | src/services/job_service.py | Encola jobs en Redis/Arq |
| Auth service | src/services/auth_service.py | JWT, bcrypt, login |
| Trip service | src/services/trip_service.py | Queries para dashboard |

### Paginas web (UI)
| Pagina | Ruta | Estado |
|--------|------|--------|
| Login | /login | Completa |
| Dashboard | / | Completa (earnings + chart + recent trips) |
| Viajes | /trips | Completa (lista + filtros + entrada manual Uber) |
| Sync | /sync | Completa (triggers FreeNow/Prima + file browser + logs) |
| Upload | /upload | Completa (CSV auto-detect + import) |
| Admin | /admin | Completa (drivers + vehicles + comisiones) |
| Validacion | /validacion | Completa (3 tabs: incidencias, VISA, combustible) |
| Liquidacion | /liquidacion | Completa (calculo + tabla + export Excel) |
| Summary | /summary | STUB - template vacio |
| Export | /export | STUB - template vacio |

### Discovery scrapers (herramientas de desarrollo)
- scrapers/freenow_discover.py - Explorar portal FreeNow
- scrapers/uber_discover.py - Explorar portal Uber Supplier

### Tests
19 archivos de tests unitarios en tests/unit/ - modelos, parsers, servicios

---

## 6. Lo que FALTA por hacer (priorizado)

### CRITICO - Arreglar produccion
| # | Tarea | Detalle |
|---|-------|---------|
| 1 | **Arreglar 502 en produccion** | Conectar taxi-api a la red Docker de Caddy. Ver seccion 2. |
| 2 | **Verificar/arreglar CI/CD** | docker compose v1 vs v2 en VPS. El pipeline puede no estar deployando. |

### ALTO - Funcionalidad core incompleta
| # | Tarea | Esfuerzo | Detalle |
|---|-------|----------|---------|
| 3 | **Auto-crear incidencias al importar** | 2h | incident_detector existe pero no se llama durante upload/sync. La cola de validacion esta siempre vacia. |
| 4 | **Auto-matching VISA al subir La Caixa** | 2h | visa_matcher existe pero no se integra en el flujo de upload. |
| 5 | **Sync automatico programado** | 4h | Arq cron jobs para sync diario a las 02:00/02:05. Ahora solo manual. |
| 6 | **Implementar /summary con datos reales** | 4h | Pagina stub, necesita summary_service con agregaciones mensuales/por conductor. |
| 7 | **Implementar /export con descargas** | 3h | Pagina stub, necesita: Excel mensual, CSV libro servicios. |
| 8 | **PDF export para liquidaciones** | 3h | Solo hay Excel export, falta PDF. |

### MEDIO - Mejoras importantes
| # | Tarea | Esfuerzo | Detalle |
|---|-------|----------|---------|
| 9 | **REST API /api/v1/** | 16h | 13 endpoints JSON (trips, drivers, summaries, sync). Ahora todo es HTML. |
| 10 | **Dashboard analytics avanzado** | 8h | EUR/km por plataforma, EUR/hora por franja, comparativa conductores. |
| 11 | **Email notifications** | 2h | Avisar admin cuando hay items pendientes en validacion. Email service existe. |
| 12 | **Auto-asignacion combustible** | 3h | Matching automatico fuel -> vehiculo/conductor por matricula. |
| 13 | **Validacion schema CSV** | 2h | Verificar columnas antes de parsear, alertar si formato cambia. |

### BAJO - Nice to have
| # | Tarea | Esfuerzo |
|---|-------|----------|
| 14 | GDPR (anonimizacion GPS 90 dias, purge tokens) | 5h |
| 15 | OAuth token encryption (Fernet) | 2h |
| 16 | Gap detection (alerta si >3 dias sin sync) | 2h |
| 17 | Rate limiting en API | 2h |

---

## 7. Bugs conocidos y workarounds

| Bug | Estado | Workaround |
|-----|--------|------------|
| 502 en produccion (Caddy no alcanza taxi-api) | ABIERTO | API funciona en localhost:8010, falta conectar redes Docker |
| docker-compose v1 `ContainerConfig` KeyError | Conocido | Usar stop/rm/up en vez de --force-recreate |
| Playwright sync API en asyncio loop | ARREGLADO | `asyncio.to_thread(scraper.run)` en tasks.py |
| entrypoint.sh ignoraba CMD override | ARREGLADO | Ahora comprueba `$#` args antes de ejecutar uvicorn |
| Prima conductor codes hardcodeados | Conocido | Map en prima_parser.py, hay que actualizar si cambian conductores |

---

## 8. Estructura de archivos clave

```
TAXI_API/
  src/
    main.py                          # FastAPI app, routers
    config.py                        # Settings (env vars)
    database.py                      # SQLAlchemy engine + session
    template_config.py               # Jinja2 config
    models/                          # SQLAlchemy models (13 archivos)
    routes/                          # Web routes (auth, admin, dashboard, trips, sync, upload, validation, liquidacion, summary, export)
    services/                        # Business logic (8 archivos)
    workers/
      settings.py                    # Arq WorkerSettings
      tasks.py                       # sync_freenow, sync_prima (async + to_thread)
    templates/                       # Jinja2 HTML templates
    static/                          # CSS, JS, favicon
  scrapers/
    freenow_scraper.py               # Playwright scraper
    prima_scraper.py                 # Playwright scraper
    uber_scraper.py                  # Skeleton
    base_scraper.py                  # Base class
    freenow_discover.py              # Dev tool
    uber_discover.py                 # Dev tool
  scripts/parsers/                   # CSV/XLSX/PDF parsers (6 archivos)
  tests/unit/                        # Unit tests (19 archivos)
  migrations/                        # Alembic migrations
  docs/plans/                        # Design docs y planes de implementacion
  docker-compose.yml                 # Dev compose
  docker-compose.prod.yml            # Prod compose (4 services)
  Dockerfile.prod                    # Production Dockerfile (Playwright + Chromium)
  entrypoint.sh                      # Checks for custom CMD, then runs uvicorn
  .github/workflows/deploy.yml       # CI/CD pipeline
  .env.example                       # Template de variables de entorno
```

---

## 9. Variables de entorno necesarias (.env en VPS)

```
DB_PASSWORD=<password-postgres>
DATABASE_URL=postgresql://taxi:<password>@taxi-db:5432/taxi_api
REDIS_URL=redis://taxi-redis:6379
SECRET_KEY=<random-string-32-chars>
FREENOW_EMAIL=<email>
FREENOW_PASSWORD=<password>
PRIMA_USER=<usuario>
PRIMA_PASSWORD=<password>
ROOT_PATH=/tools3/taxi
```

---

## 10. Historial reciente de commits

```
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
