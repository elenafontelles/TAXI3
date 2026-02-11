"""Streamlit component: OTRAS tab with email sending for PDFs."""
import os
from pathlib import Path

import streamlit as st

from scripts.utilidades.email_sender import send_email_with_attachments


def render_email_form(folder_path: str) -> None:
    """Render email form inside the OTRAS tab expander.

    Collects PDF files from the given folder and allows sending them by email.
    Should be placed inside the existing expander ("Ver contenido de una carpeta").
    """
    folder = Path(folder_path)
    pdf_files = sorted(folder.glob("*.pdf")) if folder.is_dir() else []

    if not pdf_files:
        st.info("No hay archivos PDF en esta carpeta")
        return

    st.markdown(f"**{len(pdf_files)} PDF(s)** disponibles para enviar")

    email_to = st.text_input("Email destinatario", key="otras_email_to")
    email_cc = st.text_input("CC (opcional)", key="otras_email_cc")

    if st.button("Enviar PDFs por email", key="otras_send_email"):
        if not email_to:
            st.error("Introduce un email destinatario")
            return

        smtp_host = os.environ.get("SMTP_HOST", "")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_password = os.environ.get("SMTP_PASSWORD", "")

        if not smtp_host or not smtp_user:
            st.error("SMTP no configurado. Verifica las variables de entorno SMTP_HOST y SMTP_USER.")
            return

        folder_name = folder.name
        success = send_email_with_attachments(
            to=email_to,
            subject=f"Documentos OTRAS - {folder_name}",
            body=f"Adjunto {len(pdf_files)} documento(s) PDF de la carpeta '{folder_name}'.",
            attachment_paths=pdf_files,
            cc=email_cc,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
        )

        if success:
            st.toast(f"Email enviado a {email_to} con {len(pdf_files)} adjunto(s)")
        else:
            st.error("Error al enviar el email. Revisa los logs para mas detalles.")
