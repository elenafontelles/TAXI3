"""Email alert utility for scraper/import failures."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import get_settings


def send_alert(subject: str, body: str) -> bool:
    """Send an email alert. Returns True if sent, False if SMTP not configured."""
    settings = get_settings()

    if not settings.SMTP_HOST or not settings.SMTP_USER:
        print(f"[ALERT] SMTP not configured. Subject: {subject}")
        print(f"[ALERT] Body: {body}")
        return False

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_USER
    msg["To"] = settings.ALERT_EMAIL_TO
    msg["Subject"] = f"[TAXI API] {subject}"
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[ALERT] Failed to send email: {e}")
        print(f"[ALERT] Subject: {subject}")
        print(f"[ALERT] Body: {body}")
        return False


if __name__ == "__main__":
    send_alert("Test Alert", "This is a test alert from TAXI API.")
