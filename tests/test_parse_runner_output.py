"""Tests for parse_runner_output module."""
from scripts.utilidades.parse_runner_output import parse_runner_output, RunnerDownloadResult


def test_empty_output():
    result = parse_runner_output("")
    assert result == RunnerDownloadResult(descargadas=0, ya_leidas=0)


def test_all_downloaded():
    output = (
        "Procesando notificacion 1...\n"
        "Documento guardado en: /tmp/notif_001.pdf\n"
        "Procesando notificacion 2...\n"
        "Documento guardado en: /tmp/notif_002.pdf\n"
        "Procesando notificacion 3...\n"
        "Documento guardado en: /tmp/notif_003.pdf\n"
    )
    result = parse_runner_output(output)
    assert result.descargadas == 3
    assert result.ya_leidas == 0


def test_all_already_read():
    output = (
        "Procesando notificacion 1...\n"
        "Notificacion sin contenido descargable (ya leida)\n"
        "Procesando notificacion 2...\n"
        "Notificacion sin contenido descargable (ya leida)\n"
        "Procesando notificacion 3...\n"
        "Notificacion sin contenido descargable (ya leida)\n"
    )
    result = parse_runner_output(output)
    assert result.descargadas == 0
    assert result.ya_leidas == 3


def test_mixed_results():
    output = (
        "Procesando notificacion 1...\n"
        "Documento guardado en: /tmp/notif_001.pdf\n"
        "Procesando notificacion 2...\n"
        "Notificacion sin contenido descargable (ya leida)\n"
        "Procesando notificacion 3...\n"
        "Documento guardado en: /tmp/notif_003.pdf\n"
        "Procesando notificacion 4...\n"
        "Notificacion sin contenido descargable (ya leida)\n"
        "Procesando notificacion 5...\n"
        "Documento guardado en: /tmp/notif_005.pdf\n"
    )
    result = parse_runner_output(output)
    assert result.descargadas == 3
    assert result.ya_leidas == 2


def test_acuse_not_counted():
    output = (
        "Procesando notificacion 1...\n"
        "Acuse guardado en: /tmp/acuse_001.pdf\n"
        "Procesando notificacion 2...\n"
        "Documento guardado en: /tmp/notif_002.pdf\n"
    )
    result = parse_runner_output(output)
    assert result.descargadas == 1
    assert result.ya_leidas == 0
