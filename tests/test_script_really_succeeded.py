"""Tests for _script_really_succeeded in ejecutor_tareas."""
from scripts.utilidades.ejecutor_tareas import _script_really_succeeded


def test_all_downloads_succeeded():
    """Normal case: all notifications downloaded."""
    output = (
        "Procesando notificacion 1...\n"
        "Documento guardado en: /tmp/notif_001.pdf\n"
        "Procesando notificacion 2...\n"
        "Documento guardado en: /tmp/notif_002.pdf\n"
    )
    assert _script_really_succeeded(output) is True


def test_all_already_read_is_success():
    """All notifications already read via AEAT portal — NOT a failure."""
    output = (
        "Procesando notificacion 1...\n"
        "Notificacion sin contenido descargable (ya leida)\n"
        "Procesando notificacion 2...\n"
        "Notificacion sin contenido descargable (ya leida)\n"
    )
    # "All already read" is a success — no retry needed
    assert _script_really_succeeded(output) is True


def test_mixed_downloads_and_already_read():
    """Some downloaded, some already read — still success."""
    output = (
        "Documento guardado en: /tmp/notif_001.pdf\n"
        "Notificacion sin contenido descargable (ya leida)\n"
        "Documento guardado en: /tmp/notif_003.pdf\n"
    )
    assert _script_really_succeeded(output) is True


def test_empty_output_is_failure():
    """No output at all — something went wrong."""
    assert _script_really_succeeded("") is False


def test_real_error_is_failure():
    """Connection error or crash — no downloads, no ya_leidas."""
    output = (
        "Conectando a AEAT...\n"
        "Error: Connection refused\n"
        "Traceback (most recent call last):\n"
        "  File 'runner.py', line 42\n"
        "ConnectionRefusedError: [Errno 61]\n"
    )
    assert _script_really_succeeded(output) is False


def test_partial_error_with_some_downloads():
    """Some downloads succeeded but errors also present — still success (got something)."""
    output = (
        "Documento guardado en: /tmp/notif_001.pdf\n"
        "Error procesando notificacion 2: timeout\n"
        "Documento guardado en: /tmp/notif_003.pdf\n"
    )
    assert _script_really_succeeded(output) is True


def test_only_acuse_no_documents():
    """Only acuse saved, no real documents — failure."""
    output = (
        "Acuse guardado en: /tmp/acuse_001.pdf\n"
        "Acuse guardado en: /tmp/acuse_002.pdf\n"
    )
    assert _script_really_succeeded(output) is False
