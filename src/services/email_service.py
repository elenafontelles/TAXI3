# src/services/email_service.py
"""Email notification service using aiosmtplib."""
import logging
from email.message import EmailMessage
from aiosmtplib import send
from src.config import get_settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email. Returns True on success."""
    settings = get_settings()
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("SMTP not configured, skipping email")
        return False

    msg = EmailMessage()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        await send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=True,
        )
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


async def notify_pending_validations(count: int):
    """Notify admin about pending validation items."""
    settings = get_settings()
    if not settings.ALERT_EMAIL_TO:
        return

    await send_email(
        to=settings.ALERT_EMAIL_TO,
        subject=f"TAXI API: {count} validacion(es) pendiente(s)",
        body=(
            f"Se han detectado {count} elemento(s) pendiente(s) de validacion.\n\n"
            f"Tipos posibles:\n"
            f"- Incidencias (viajes con 0 km / < 30s)\n"
            f"- Pagos VISA sin enlazar a viaje\n"
            f"- Gastos combustible sin asignar\n\n"
            f"Revisa la cola de validacion en la aplicacion."
        ),
    )
