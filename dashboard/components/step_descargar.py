"""Streamlit component: download step with detailed feedback."""
import streamlit as st

from scripts.utilidades.parse_runner_output import parse_runner_output


def render_download_feedback(runner_output: str) -> None:
    """Show detailed download feedback based on runner output.

    Displays counts of downloaded documents and already-read notifications
    instead of a generic success/error message.
    """
    result = parse_runner_output(runner_output)

    parts = []
    if result.descargadas > 0:
        parts.append(f"{result.descargadas} descargada{'s' if result.descargadas != 1 else ''}")
    else:
        parts.append("0 descargadas")

    if result.ya_leidas > 0:
        parts.append(f"{result.ya_leidas} ya leida{'s' if result.ya_leidas != 1 else ''}")

    message = ", ".join(parts)

    if result.descargadas > 0 and result.ya_leidas == 0:
        st.success(message)
    elif result.descargadas == 0 and result.ya_leidas > 0:
        st.info(message)
    elif result.descargadas > 0 and result.ya_leidas > 0:
        st.warning(message)
    else:
        st.error("No se pudo descargar ninguna notificacion")
