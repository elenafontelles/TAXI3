# src/workers/tasks.py
"""Arq job tasks for scraper synchronization."""
import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

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

        # Run scraper in a thread (Playwright sync API can't run inside asyncio loop)
        from scrapers.freenow_scraper import FreeNowScraper
        scraper = FreeNowScraper(start_date=sd, end_date=ed)
        csv_path = await asyncio.to_thread(scraper.run)

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

        # Run scraper in a thread (Playwright sync API can't run inside asyncio loop)
        from scrapers.prima_scraper import PrimaScraper
        scraper = PrimaScraper(start_date=sd, end_date=ed)
        csv_path = await asyncio.to_thread(scraper.run)

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


async def scheduled_gdpr_cleanup(ctx):
    """Cron job: anonymize old GPS data and purge expired tokens."""
    logger.info("Running scheduled GDPR cleanup")

    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        from src.services.gdpr_service import anonymize_old_gps, purge_expired_tokens
        gps_count = anonymize_old_gps(session)
        token_count = purge_expired_tokens(session)
        logger.info(f"GDPR cleanup done: {gps_count} trips anonymized, {token_count} tokens purged")
        return {"gps_anonymized": gps_count, "tokens_purged": token_count}
    except Exception as e:
        logger.exception(f"GDPR cleanup failed: {e}")
        return {"error": str(e)}
    finally:
        session.close()


async def scheduled_gap_check(ctx):
    """Cron job: check for sync gaps and alert admin."""
    logger.info("Running scheduled sync gap check")

    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        from src.services.gap_detector import check_sync_gaps
        gaps = check_sync_gaps(session)

        if gaps:
            platforms = ", ".join(
                f"{g['platform']} ({g['days_since']}d)" for g in gaps
            )
            logger.warning(f"Sync gaps detected: {platforms}")

            from src.services.email_service import send_email
            from src.config import get_settings
            settings = get_settings()
            if settings.ALERT_EMAIL_TO:
                body = "Se han detectado brechas en la sincronizacion:\n\n"
                for g in gaps:
                    last = g["last_sync"] or "nunca"
                    body += f"- {g['platform'].upper()}: ultimo sync exitoso: {last} ({g['days_since']} dias)\n"
                body += f"\nUmbral configurado: {3} dias.\nRevisa la pagina de sync en la aplicacion."
                await send_email(
                    to=settings.ALERT_EMAIL_TO,
                    subject=f"TAXI API: alerta de sync gap ({len(gaps)} plataforma(s))",
                    body=body,
                )

        return {"gaps": gaps}
    except Exception as e:
        logger.exception(f"Gap check failed: {e}")
        return {"error": str(e)}
    finally:
        session.close()


async def scheduled_sync_freenow(ctx):
    """Cron job: sync FreeNow for yesterday's data."""
    yesterday = date.today() - timedelta(days=1)
    logger.info(f"Scheduled FreeNow sync for {yesterday}")

    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        log = SyncLog(
            source="freenow",
            sync_type="scheduled",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(log)
        session.commit()
        log_id = log.id
    finally:
        session.close()

    return await sync_freenow(ctx, log_id, yesterday.isoformat(), yesterday.isoformat())


async def scheduled_sync_prima(ctx):
    """Cron job: sync Prima for yesterday's data."""
    yesterday = date.today() - timedelta(days=1)
    logger.info(f"Scheduled Prima sync for {yesterday}")

    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        log = SyncLog(
            source="prima",
            sync_type="scheduled",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(log)
        session.commit()
        log_id = log.id
    finally:
        session.close()

    return await sync_prima(ctx, log_id, yesterday.isoformat(), yesterday.isoformat())
