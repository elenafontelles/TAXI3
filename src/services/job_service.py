# src/services/job_service.py
"""Job queue service for enqueueing scraper tasks."""
import logging
from datetime import date

from arq import create_pool

from src.workers.settings import get_redis_settings

logger = logging.getLogger(__name__)


async def enqueue_sync(source: str, log_id: int, start_date: date, end_date: date,
                       account_label: str = "") -> str:
    """Enqueue a sync job for the given source.

    Args:
        source: Platform name ('freenow' or 'prima')
        log_id: SyncLog record ID
        start_date: Start date for sync
        end_date: End date for sync
        account_label: Optional account label (for multi-account platforms)

    Returns:
        Job ID string
    """
    redis = await create_pool(get_redis_settings())
    try:
        task_name = f"sync_{source}"  # sync_freenow or sync_prima
        job = await redis.enqueue_job(
            task_name,
            log_id,
            start_date.isoformat(),
            end_date.isoformat(),
            account_label,
        )
        logger.info(f"Enqueued {task_name} job {job.job_id} for log_id={log_id} account={account_label or 'default'}")
        return job.job_id
    finally:
        await redis.close()
