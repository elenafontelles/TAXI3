# TAXI API - Simplified Architecture Design

**Date:** 1 February 2026
**Status:** Approved
**Context:** Brainstorming session reviewing TAXI_API_SPEC.md for technical accuracy and over-engineering

---

## Decisions Made

### User Profile
- 5 users total: 2 owners (Ivan, Elena) + 3 drivers
- Primary use: accounting automation for tax filings
- Secondary use: drivers check daily income on their phone
- Not a real-time operational tool

### Hosting
- Existing VPS (same server as other projects)
- Docker Compose deployment

---

## System Overview

Billing consolidation system for 3 taxis. Collects trip data from Uber, FreeNow, and Prima via Playwright browser automation, stores it in PostgreSQL, and serves a mobile-friendly web dashboard.

### Data Flow

```
Playwright scrapers (cron, 02:00 AM daily)
        |
        v
  CSV files saved to /imports/
        |
        v
  Python parser --> PostgreSQL (trips table)
        |
        v
  FastAPI + Jinja2 dashboard (mobile-friendly)
```

If a scraper fails: email alert to Ivan. Manual CSV upload as fallback through the web UI.

### Stack

- Python 3.11 + FastAPI + Jinja2 + Chart.js
- PostgreSQL 15
- Playwright (browser automation for scraping)
- Docker Compose (on existing VPS)
- Cron (scheduling)
- Bootstrap 5 (responsive CSS)
- Alembic (database migrations)

### What is NOT in the stack

- No Celery, no Redis
- No React frontend
- No Prometheus, Grafana, or Alertmanager
- No OAuth 2.0 (Uber API not available)
- No distributed tracing

---

## Data Sources (Verified)

| Platform | Method | Status |
|----------|--------|--------|
| Uber | Playwright scraper on driver.uber.com | Verified: API restricted, CSV only |
| FreeNow | Playwright scraper on portal.free-now.com | Confirmed: no public API |
| Prima | Playwright scraper on Taxitronic cloud | Pending verification |

All three sources: Playwright scraper as primary, manual CSV upload as fallback.

---

## Data Model

All 10 tables from the original TAXI_API_SPEC.md are kept:

| Table | Purpose |
|-------|---------|
| `owners` | Ivan and Elena |
| `drivers` | All drivers including owners who drive |
| `vehicles` | The 3 taxis |
| `trips` | Every trip from every source (core table) |
| `shifts` | Prima shift data (km, hours, speed) |
| `daily_summaries` | Pre-calculated daily totals for dashboard |
| `sync_logs` | Record of each scraper/import run |
| `freenow_imports` | Tracking imported FreeNow files |
| `platform_tokens` | Reserved for future API integrations (FreeNow) |
| `dsr_requests` | Reserved for future GDPR automation |

Key simplification: deduplication relies on `external_id` unique index only. No temporal-spatial heuristic engine or manual review queue.

---

## Scrapers

Three standalone Python scripts, one per platform. Triggered by cron.

```
cron (02:00 AM daily)
  |- python scrapers/uber_scraper.py
  |- python scrapers/freenow_scraper.py
  +- python scrapers/prima_scraper.py
```

Each scraper:
1. Launches headless Chromium via Playwright
2. Logs in to the platform (credentials from .env)
3. Navigates to the export/history page
4. Downloads yesterday's data
5. Saves to /imports/<source>_YYYY-MM-DD.csv
6. Exits browser

Then a parser script runs:

```
cron (02:15 AM daily)
  +- python scripts/import_csvs.py
      |- Parse new files in /imports/
      |- Normalize to common format
      |- Insert into trips table (ON CONFLICT skip duplicates)
      |- Update daily_summaries
      |- Log result to sync_logs
      +- Send email if anything failed
```

Credentials stored in .env, loaded via Pydantic Settings.

---

## Dashboard Pages

Server-rendered HTML. No SPA, no separate API.

| Page | Who sees it | What it shows |
|------|-------------|---------------|
| `/login` | Everyone | Email + password form |
| `/` | Everyone | Today's earnings, this week, this month (filtered by role) |
| `/trips` | Everyone | List of trips with filters. Drivers see only theirs |
| `/summary` | Owners + Admin | Daily/monthly breakdown by driver, vehicle, platform |
| `/export` | Owners + Admin | Download CSV/Excel for tax filing, select date range |
| `/upload` | Admin only | Drag-and-drop CSV upload (manual fallback) |
| `/sync` | Admin only | Status of last scraper runs, button to trigger manual re-run |

Tech: FastAPI + Jinja2Templates + Bootstrap 5 + Chart.js

---

## Authentication

- JWT tokens with RBAC
- 3 roles: admin (Ivan), owner (Elena), driver (employees)
- Admin: full access
- Owner: sees own vehicles and drivers
- Driver: sees only own earnings

---

## Alerting

- Email alerts on scraper failure
- Python smtplib or a service like SendGrid
- No Prometheus, no Alertmanager, no Telegram

---

## Project Structure

```
taxi-api/
|- docker-compose.yml
|- Dockerfile
|- requirements.txt
|- .env.example
|- .gitignore
|
|- src/
|   |- main.py                  # FastAPI app entry point
|   |- config.py                # Pydantic Settings (.env loading)
|   |- database.py              # SQLAlchemy engine + session
|   |
|   |- models/                  # SQLAlchemy table definitions
|   |   |- owner.py
|   |   |- driver.py
|   |   |- vehicle.py
|   |   |- trip.py
|   |   |- shift.py
|   |   +- ...
|   |
|   |- routes/                  # FastAPI routes (return HTML)
|   |   |- auth.py
|   |   |- dashboard.py
|   |   |- trips.py
|   |   |- summary.py
|   |   |- export.py
|   |   |- upload.py
|   |   +- sync.py
|   |
|   |- services/                # Business logic
|   |   |- auth_service.py
|   |   |- trip_service.py
|   |   +- summary_service.py
|   |
|   |- templates/               # Jinja2 HTML templates
|   |   |- base.html
|   |   |- login.html
|   |   |- dashboard.html
|   |   +- ...
|   |
|   +- static/                  # CSS, JS, images
|       |- style.css
|       +- chart-config.js
|
|- scrapers/                    # Playwright scripts
|   |- uber_scraper.py
|   |- freenow_scraper.py
|   +- prima_scraper.py
|
|- scripts/
|   |- import_csvs.py           # Parse CSVs to database
|   +- send_email.py            # Alert utility
|
|- migrations/                  # Alembic database migrations
|
|- imports/                     # CSV landing folder
|
+- tests/
    |- unit/
    |- integration/
    +- e2e/
```

No Clean Architecture layers. Flat models/routes/services structure (standard FastAPI).

---

## Removed from Original Spec

| Component | Reason |
|-----------|--------|
| Celery + Redis | Cron + scripts is sufficient |
| React frontend | Jinja2 templates, no build pipeline |
| Prometheus + Grafana + Alertmanager | Email on failure is enough |
| OAuth 2.0 flow for Uber | API not available |
| Token encryption (Fernet) | No tokens to manage |
| SLOs/SLA definitions | 5 users, not needed |
| Deduplication engine (heuristics) | external_id unique index is enough |
| Manual dedup review queue | Not needed at this scale |
| DSR automation workflow | Handle manually if needed |
| Clean Architecture layers | Flat structure, easier to learn |
| Cursor-based pagination | Simple offset pagination, small dataset |
| Rate limiting on own API | 5 users |
| HMAC webhook validation | No webhooks |
| OpenTelemetry / distributed tracing | Single service |

## Kept from Original Spec

- PostgreSQL schema (all 10 tables)
- JWT authentication + RBAC (3 roles)
- Docker Compose deployment
- Alembic migrations
- GPS anonymization cron function
- GDPR data retention policy (7 years financial, 90 days GPS)
- TDD testing approach

## Simplified from Original Spec

| Component | Original | Simplified |
|-----------|----------|------------|
| Data ingestion | API + CSV connectors | Playwright scrapers + CSV parser |
| Alerting | Prometheus + Alertmanager + Telegram | Python + email |
| Dashboard | React + Recharts SPA | Jinja2 + Chart.js server-rendered |
| Frontend delivery | Separate API + frontend build | Server-rendered HTML |
| Sync orchestration | Celery chord (parallel + chain) | Sequential cron jobs |

---

## Future Considerations (not now)

- FreeNow API integration if they open one (platform_tokens table ready)
- Uber API if access is granted (apply at developer.uber.com/products/drivers)
- WhatsApp alerts if email proves insufficient
- Separate REST API if a mobile app is ever needed
