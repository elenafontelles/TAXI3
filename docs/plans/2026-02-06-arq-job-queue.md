# Arq Job Queue Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace threading-based scraper execution with Arq async job queue for reliability and observability.

**Architecture:** FastAPI → Redis → Arq Worker → Postgres. Jobs are enqueued via Redis, processed by dedicated worker container, results stored in SyncLog table.

**Tech Stack:** Arq 0.26+, Redis 5.0+, Docker Compose

---

## Task 1: Add Dependencies

**Files:**
- Modify: `requirements.txt`

**Step 1:** Add arq and redis packages

```
# Job queue
arq>=0.26
redis>=5.0
```

**Step 2:** Install locally

```bash
pip install arq redis
```

---

## Task 2: Create Worker Settings

**Files:**
- Create: `src/workers/__init__.py`
- Create: `src/workers/settings.py`

**Code for settings.py:**

```python
"""Arq worker settings."""
from arq.connections import RedisSettings
from src.config import get_settings

def get_redis_settings() -> RedisSettings:
    settings = get_settings()
    return RedisSettings.from_dsn(settings.REDIS_URL)

class WorkerSettings:
    redis_settings = get_redis_settings()
    max_jobs = 2  # Limit concurrent jobs (scrapers are heavy)
    job_timeout = 600  # 10 minutes max per job
    keep_result = 3600  # Keep results for 1 hour
```

---

## Task 3: Create Job Tasks

**Files:**
- Create: `src/workers/tasks.py`

**Code:**

```python
"""Arq job tasks for scraper synchronization."""
import logging
from datetime import date
from arq import Retry
from sqlalchemy.orm import sessionmaker
from src.database import get_engine
from src.models.sync_log import SyncLog

logger = logging.getLogger(__name__)

async def sync_freenow(ctx, log_id: int, start_date: str, end_date: str):
    """Run FreeNow scraper and import results."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        log = session.get(SyncLog, log_id)
        if not log:
            logger.error(f"SyncLog {log_id} not found")
            return {"status": "error", "message": "Log not found"}

        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)

        from scrapers.freenow_scraper import FreeNowScraper
        scraper = FreeNowScraper(start_date=sd, end_date=ed)
        csv_path = scraper.run()

        if csv_path:
            from src.services.freenow_import import import_freenow_csv
            stats = import_freenow_csv(csv_path, session)
            log.status = "completed"
            log.records_imported = stats.get("imported", 0)
            log.result_message = f"Imported {stats.get('imported', 0)} trips"
        else:
            log.status = "failed"
            log.result_message = "Scraper returned no file"

        session.commit()
        return {"status": log.status, "records": log.records_imported}
    except Exception as e:
        logger.exception(f"sync_freenow failed: {e}")
        if session:
            log = session.get(SyncLog, log_id)
            if log:
                log.status = "failed"
                log.result_message = str(e)[:500]
                session.commit()
        raise Retry(defer=60)  # Retry after 1 minute
    finally:
        session.close()

async def sync_prima(ctx, log_id: int, start_date: str, end_date: str):
    """Run Prima scraper and import results."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        log = session.get(SyncLog, log_id)
        if not log:
            logger.error(f"SyncLog {log_id} not found")
            return {"status": "error", "message": "Log not found"}

        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)

        from scrapers.prima_scraper import PrimaScraper
        scraper = PrimaScraper(start_date=sd, end_date=ed)
        csv_path = scraper.run()

        if csv_path:
            from src.services.prima_import import import_prima_csv
            stats = import_prima_csv(csv_path, session)
            log.status = "completed"
            log.records_imported = stats.get("imported", 0)
            log.result_message = f"Imported {stats.get('imported', 0)} trips"
        else:
            log.status = "failed"
            log.result_message = "Scraper returned no file"

        session.commit()
        return {"status": log.status, "records": log.records_imported}
    except Exception as e:
        logger.exception(f"sync_prima failed: {e}")
        if session:
            log = session.get(SyncLog, log_id)
            if log:
                log.status = "failed"
                log.result_message = str(e)[:500]
                session.commit()
        raise Retry(defer=60)
    finally:
        session.close()
```

---

## Task 4: Create Job Service

**Files:**
- Create: `src/services/job_service.py`

**Code:**

```python
"""Job queue service for enqueueing scraper tasks."""
from datetime import date
from arq import create_pool
from src.workers.settings import get_redis_settings

async def enqueue_sync(source: str, log_id: int, start_date: date, end_date: date):
    """Enqueue a sync job for the given source."""
    redis = await create_pool(get_redis_settings())

    task_name = f"sync_{source}"  # sync_freenow or sync_prima
    job = await redis.enqueue_job(
        task_name,
        log_id,
        start_date.isoformat(),
        end_date.isoformat(),
    )
    await redis.close()
    return job.job_id
```

---

## Task 5: Update Sync Routes

**Files:**
- Modify: `src/routes/sync.py`

**Changes:**
- Remove threading imports and _run_freenow_sync / _run_prima_sync functions
- Replace thread.start() with await enqueue_sync()
- Make route async if not already

---

## Task 6: Update Docker Compose

**Files:**
- Modify: `docker-compose.yml`

**Add Redis service:**

```yaml
  redis:
    image: redis:7-alpine
    container_name: taxi-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
```

**Add Worker service:**

```yaml
  worker:
    build: .
    container_name: taxi-worker
    command: arq src.workers.settings.WorkerSettings
    restart: unless-stopped
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./imports:/app/imports
```

**Add volume:**

```yaml
volumes:
  postgres_data:
  redis_data:
```

---

## Task 7: Add Redis Config

**Files:**
- Modify: `src/config.py`
- Modify: `.env.example`

**Add to Settings class:**

```python
REDIS_URL: str = "redis://localhost:6379"
```

**Add to .env.example:**

```
REDIS_URL=redis://redis:6379
```

---

## Task 8: Update Worker Settings with Functions

**Files:**
- Modify: `src/workers/settings.py`

**Add functions list:**

```python
from src.workers.tasks import sync_freenow, sync_prima

class WorkerSettings:
    functions = [sync_freenow, sync_prima]
    # ... rest of settings
```

---

## Task 9: Test Complete Flow

**Steps:**
1. Start Redis locally or via Docker
2. Run worker: `arq src.workers.settings.WorkerSettings`
3. Hit sync endpoint
4. Verify job is processed and SyncLog updated
