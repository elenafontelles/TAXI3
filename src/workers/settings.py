# src/workers/settings.py
"""Arq worker settings and configuration."""
from arq.connections import RedisSettings


def get_redis_settings() -> RedisSettings:
    """Get Redis settings from environment config."""
    from src.config import get_settings
    settings = get_settings()
    return RedisSettings.from_dsn(settings.REDIS_URL)


class WorkerSettings:
    """Arq worker configuration."""

    # Import tasks here to register them
    from src.workers.tasks import sync_freenow, sync_prima

    functions = [sync_freenow, sync_prima]
    redis_settings = get_redis_settings()
    max_jobs = 2  # Limit concurrent jobs (scrapers are resource-heavy)
    job_timeout = 600  # 10 minutes max per job
    keep_result = 3600  # Keep results for 1 hour
