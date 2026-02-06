# src/workers/tasks.py
"""Arq job tasks for scraper synchronization."""
import logging
from datetime import date, datetime, timezone

from sqlalchemy.orm import sessionmaker

from src.database import get_engine
from src.models.sync_log import SyncLog

logger = logging.getLogger(__name__)


async def sync_freenow(ctx, log_id: int, start_date: str, end_date: str):
    """Run FreeNow scraper and import results.

    Args:
        ctx: Arq context (contains redis connection)
        log_id: SyncLog record ID to update
        start_date: ISO format date string
        end_date: ISO format date string

    Returns:
        Dict with status and record counts
    """
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        log = session.get(SyncLog, log_id)
        if not log:
            logger.error(f"SyncLog {log_id} not found")
            return {"status": "error", "message": "Log not found"}

        started_at = log.started_at
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)

        # Import scraper and run
        from scrapers.freenow_scraper import FreeNowScraper
        scraper = FreeNowScraper(start_date=sd, end_date=ed)
        csv_path = scraper.run()

        if not csv_path:
            log.status = "error"
            log.error_message = "No se pudo descargar el CSV (sin datos o credenciales incorrectas)"
            log.completed_at = datetime.now(timezone.utc)
            log.duration_seconds = (log.completed_at - started_at).total_seconds()
            session.commit()
            return {"status": "error", "message": log.error_message}

        # Import the CSV
        from src.routes.sync import _import_freenow_csv
        created, skipped, unmatched = _import_freenow_csv(csv_path, session)

        log.status = "success"
        log.records_found = created + skipped + unmatched
        log.records_created = created
        log.records_skipped = skipped
        log.completed_at = datetime.now(timezone.utc)
        log.duration_seconds = (log.completed_at - started_at).total_seconds()
        if unmatched:
            log.error_message = f"{unmatched} viajes sin conductor/vehiculo asignado"
        session.commit()

        return {
            "status": "success",
            "created": created,
            "skipped": skipped,
            "unmatched": unmatched,
        }

    except Exception as e:
        logger.exception(f"sync_freenow failed: {e}")
        try:
            log = session.get(SyncLog, log_id)
            if log:
                log.status = "error"
                log.error_message = str(e)[:500]
                log.completed_at = datetime.now(timezone.utc)
                if log.started_at:
                    log.duration_seconds = (log.completed_at - log.started_at).total_seconds()
                session.commit()
        except Exception:
            logger.exception("Failed to update SyncLog after error")
        raise  # Re-raise to let Arq handle retry if configured
    finally:
        session.close()


async def sync_prima(ctx, log_id: int, start_date: str, end_date: str):
    """Run Prima scraper and import results.

    Args:
        ctx: Arq context (contains redis connection)
        log_id: SyncLog record ID to update
        start_date: ISO format date string
        end_date: ISO format date string

    Returns:
        Dict with status and record counts
    """
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        log = session.get(SyncLog, log_id)
        if not log:
            logger.error(f"SyncLog {log_id} not found")
            return {"status": "error", "message": "Log not found"}

        started_at = log.started_at
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)

        # Import scraper and run
        from scrapers.prima_scraper import PrimaScraper
        scraper = PrimaScraper(start_date=sd, end_date=ed)
        csv_path = scraper.run()

        if not csv_path:
            log.status = "error"
            log.error_message = "No se pudo descargar el CSV (sin datos o credenciales incorrectas)"
            log.completed_at = datetime.now(timezone.utc)
            log.duration_seconds = (log.completed_at - started_at).total_seconds()
            session.commit()
            return {"status": "error", "message": log.error_message}

        # Import the CSV
        from src.routes.sync import _import_prima_csv
        created, skipped, unmatched = _import_prima_csv(csv_path, session)

        # Cross-match Prima trips (amount=0) with FreeNow/Uber
        from src.services.trip_matcher import cross_match_trips
        match_stats = cross_match_trips(session)

        log.status = "success"
        log.records_found = created + skipped + unmatched
        log.records_created = created
        log.records_skipped = skipped
        log.records_updated = match_stats["matched"]  # trips linked
        log.completed_at = datetime.now(timezone.utc)
        log.duration_seconds = (log.completed_at - started_at).total_seconds()

        messages = []
        if unmatched:
            messages.append(f"{unmatched} viajes sin conductor/vehiculo")
        if match_stats["matched"]:
            messages.append(f"{match_stats['matched']} enlazados con app")
        if match_stats["no_match"]:
            messages.append(f"{match_stats['no_match']} sin enlace (posible Uber)")
        if messages:
            log.error_message = ", ".join(messages)
        session.commit()

        return {
            "status": "success",
            "created": created,
            "skipped": skipped,
            "unmatched": unmatched,
            "matched": match_stats["matched"],
        }

    except Exception as e:
        logger.exception(f"sync_prima failed: {e}")
        try:
            log = session.get(SyncLog, log_id)
            if log:
                log.status = "error"
                log.error_message = str(e)[:500]
                log.completed_at = datetime.now(timezone.utc)
                if log.started_at:
                    log.duration_seconds = (log.completed_at - log.started_at).total_seconds()
                session.commit()
        except Exception:
            logger.exception("Failed to update SyncLog after error")
        raise
    finally:
        session.close()
