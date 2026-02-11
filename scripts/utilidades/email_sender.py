"""Send emails with PDF attachments via SMTP."""
import logging
import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def build_email_message(
    to: str,
    subject: str,
    body: str,
    attachment_paths: list[Path],
    cc: str = "",
    from_addr: str = "",
) -> MIMEMultipart:
    """Build a MIME message with PDF attachments.

    Raises ValueError if no attachments or invalid email.
    """
    if not attachment_paths:
        raise ValueError("Debe adjuntar al menos un archivo")

    if not _EMAIL_RE.match(to):
        raise ValueError(f"Direccion de email invalida: {to}")

    if cc and not _EMAIL_RE.match(cc):
        raise ValueError(f"Direccion de email CC invalida: {cc}")

    msg = MIMEMultipart("mixed")
    msg["To"] = to
    msg["Subject"] = subject
    msg["From"] = from_addr or "noreply@taxi-api.local"
    if cc:
        msg["Cc"] = cc

    msg.attach(MIMEText(body, "plain", "utf-8"))

    for path in attachment_paths:
        path = Path(path)
        with open(path, "rb") as f:
            part = MIMEApplication(f.read(), Name=path.name)
        part["Content-Disposition"] = f'attachment; filename="{path.name}"'
        msg.attach(part)

    return msg


def send_email_with_attachments(
    to: str,
    subject: str,
    body: str,
    attachment_paths: list[Path],
    cc: str = "",
    smtp_host: str = "",
    smtp_port: int = 587,
    smtp_user: str = "",
    smtp_password: str = "",
) -> bool:
    """Send an email with file attachments via SMTP + STARTTLS.

    Returns True on success, False on failure.
    """
    msg = build_email_message(
        to=to,
        subject=subject,
        body=body,
        attachment_paths=attachment_paths,
        cc=cc,
        from_addr=smtp_user,
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logger.info("Email enviado a %s con %d adjuntos", to, len(attachment_paths))
        return True
    except Exception:
        logger.exception("Error enviando email a %s", to)
        return False
