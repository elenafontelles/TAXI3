# src/workers/settings.py
"""Arq worker settings and configuration."""
from arq.connections import RedisSettings
from arq.cron import cron


def get_redis_settings() -> RedisSettings:
    """Get Redis settings from environment config."""
    from src.config import get_settings
    settings = get_settings()
    return RedisSettings.from_dsn(settings.REDIS_URL)


class WorkerSettings:
    """Arq worker configuration."""

    # Import tasks here to register them
    from src.workers.tasks import sync_freenow, sync_prima
    from src.workers.tasks import scheduled_sync_freenow, scheduled_sync_prima
    from src.workers.tasks import scheduled_gdpr_cleanup, scheduled_gap_check

    functions = [sync_freenow, sync_prima]
    cron_jobs = [
        cron(scheduled_sync_freenow, hour=2, minute=0),    # Daily at 02:00 UTC
        cron(scheduled_sync_prima, hour=2, minute=5),       # Daily at 02:05 UTC
        cron(scheduled_gdpr_cleanup, hour=3, minute=0),     # Daily at 03:00 UTC
        cron(scheduled_gap_check, hour=8, minute=0),        # Daily at 08:00 UTC
    ]
    redis_settings = get_redis_settings()
    max_jobs = 2  # Limit concurrent jobs (scrapers are resource-heavy)
    job_timeout = 600  # 10 minutes max per job
    keep_result = 3600  # Keep results for 1 hour
