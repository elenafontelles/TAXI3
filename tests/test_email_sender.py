"""Tests for email_sender module."""
import email
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.utilidades.email_sender import (
    build_email_message,
    send_email_with_attachments,
)


@pytest.fixture
def tmp_pdfs(tmp_path):
    """Create temporary PDF files for testing."""
    files = []
    for i in range(3):
        p = tmp_path / f"doc_{i}.pdf"
        p.write_bytes(b"%PDF-1.4 fake content " + str(i).encode())
        files.append(p)
    return files


def test_build_email_message(tmp_pdfs):
    msg = build_email_message(
        to="recipient@example.com",
        subject="Test Subject",
        body="Test body content",
        attachment_paths=tmp_pdfs,
    )
    assert msg["To"] == "recipient@example.com"
    assert msg["Subject"] == "Test Subject"
    assert msg["From"] is not None

    # Check MIME structure - should be multipart/mixed
    assert msg.get_content_type() == "multipart/mixed"

    parts = list(msg.walk())
    # First is the multipart container, then text body, then 3 attachments
    text_parts = [p for p in parts if p.get_content_type() == "text/plain"]
    assert len(text_parts) == 1
    assert "Test body content" in text_parts[0].get_payload(decode=True).decode()

    attachment_parts = [
        p for p in parts if p.get_content_disposition() == "attachment"
    ]
    assert len(attachment_parts) == 3
    filenames = [p.get_filename() for p in attachment_parts]
    assert "doc_0.pdf" in filenames
    assert "doc_1.pdf" in filenames
    assert "doc_2.pdf" in filenames


def test_build_email_with_cc(tmp_pdfs):
    msg = build_email_message(
        to="recipient@example.com",
        subject="Test",
        body="Body",
        attachment_paths=tmp_pdfs,
        cc="cc@example.com",
    )
    assert msg["Cc"] == "cc@example.com"


def test_no_attachments_raises():
    with pytest.raises(ValueError, match="adjuntar"):
        build_email_message(
            to="recipient@example.com",
            subject="Test",
            body="Body",
            attachment_paths=[],
        )


def test_invalid_email_raises(tmp_pdfs):
    with pytest.raises(ValueError, match="email"):
        build_email_message(
            to="not-an-email",
            subject="Test",
            body="Body",
            attachment_paths=tmp_pdfs,
        )


@patch("scripts.utilidades.email_sender.smtplib.SMTP")
def test_send_email_success(mock_smtp_class, tmp_pdfs):
    mock_smtp = MagicMock()
    mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

    result = send_email_with_attachments(
        to="recipient@example.com",
        subject="Test",
        body="Body",
        attachment_paths=tmp_pdfs,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_user="user@gmail.com",
        smtp_password="app-password",
    )
    assert result is True
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("user@gmail.com", "app-password")
    mock_smtp.send_message.assert_called_once()
