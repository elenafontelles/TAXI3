# Deployment Design: TAXI API to Production VPS

**Date:** 2026-02-03
**Status:** Validated via multi-model consensus (Gemini 2.5 Pro 9/10, GPT-5.2 8/10)

## Overview

Deploy the TAXI API (FastAPI + PostgreSQL + Playwright/Chromium) to a VPS behind an existing Caddy reverse proxy at `keonycs.com/tools3/taxi/`, with CI/CD via GitHub Actions.

## Architecture

```
Internet
  │
  ▼
Caddy (keonycs.com, auto-SSL)
  │  handle /tools3/taxi/*
  │  reverse_proxy taxi-api:8000
  ▼
┌─────────────────────────────┐
│  Docker Compose (prod)      │
│                             │
│  taxi-api (:8000 internal)  │
│    FastAPI + Playwright     │
│    ROOT_PATH=/tools3/taxi   │
│    Non-root user            │
│                             │
│  taxi-db (:5432 internal)   │
│    PostgreSQL 15            │
│    Named volume             │
│    No public port           │
└─────────────────────────────┘
```

## Key Decisions

### 1. Subpath Routing (handle, not handle_path)

Caddy `handle` (NOT `handle_path`) so the prefix is NOT stripped. FastAPI receives the full path `/tools3/taxi/...` and uses `ROOT_PATH=/tools3/taxi` to generate correct URLs for templates, redirects, static files, and OpenAPI docs.

This avoids the double-prefix / missing-prefix bugs that occur when combining `handle_path` (strip) with `ROOT_PATH`.

### 2. CI/CD: GHCR + SSH Deploy

```
git push main
  → GitHub Actions:
      1. Build Docker image
      2. Push to ghcr.io/ivantintore/taxi-api:latest
      3. SSH to VPS
      4. docker pull ghcr.io/ivantintore/taxi-api:latest
      5. docker compose -f docker-compose.prod.yml run --rm taxi-api alembic upgrade head
      6. docker compose -f docker-compose.prod.yml up -d
```

SSH deploy chosen over Watchtower for:
- Explicit control over deployment timing
- Ability to run migrations before restart
- Traceability via GitHub Actions logs

### 3. Database Migrations

Alembic runs as an explicit step in the deploy pipeline, BEFORE restarting the API container. This ensures schema is always in sync with application code.

### 4. Playwright/Chromium

Use the official `mcr.microsoft.com/playwright/python` base image to avoid manual dependency management. Accept the large image size as a trade-off for reliability.

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `docker-compose.prod.yml` | Create | Production Compose with GHCR image |
| `.github/workflows/deploy.yml` | Create | CI/CD pipeline |
| `Dockerfile.prod` | Create | Production Dockerfile (Playwright base image) |
| `entrypoint.sh` | Create | Run migrations + start uvicorn |
| `src/main.py` | Modify | Add ROOT_PATH from env var |
| `Caddyfile snippet` | Document | For manual addition to VPS Caddy config |

## Security Hardening

- API container binds only to Docker internal network (no host port exposure)
- PostgreSQL: no public port, strong random password in `.env`
- Non-root user in API container
- GitHub Secrets for SSH_KEY, VPS_HOST, VPS_USER
- `.env` on VPS only (not in repo, not in image)
- Deploy key with minimal permissions
- pg_dump backup cron on VPS

## Caddy Config (add to VPS Caddyfile)

```caddyfile
handle /tools3/taxi/* {
    reverse_proxy taxi-api:8000
}
```

## Environment Variables (VPS .env)

```
DATABASE_URL=postgresql://taxi:STRONG_RANDOM_PASSWORD@taxi-db:5432/taxi
SECRET_KEY=...
FREENOW_EMAIL=...
FREENOW_PASSWORD=...
```
