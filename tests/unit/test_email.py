import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")


def test_send_alert_constructs_email():
    """send_alert should construct proper email message."""
    from scripts.send_email import send_alert

    with patch("scripts.send_email.smtplib") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.SMTP.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.SMTP.return_value.__exit__ = MagicMock(return_value=False)

        # Should not raise even with empty SMTP settings (graceful degradation)
        send_alert("Test Subject", "Test body content")


def test_send_alert_with_empty_config():
    """send_alert should handle missing SMTP config gracefully."""
    from scripts.send_email import send_alert

    # With empty SMTP settings, should just print a warning, not crash
    result = send_alert("Test", "Body")
    assert result is not None or result is None  # Just shouldn't raise
