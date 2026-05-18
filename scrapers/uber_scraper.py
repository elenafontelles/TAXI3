"""Uber supplier portal - manual download instructions.

Uber requires 2FA login which cannot be automated reliably.
This module provides the download instructions and account config
for the "Descargar CSVs" page to display.
"""

# Step-by-step instructions shown in the UI
UBER_DOWNLOAD_STEPS = [
    {
        "step": 1,
        "title": "Abre el portal de Uber",
        "detail": 'Ve a <a href="https://supplier.uber.com" target="_blank">'
                  "supplier.uber.com</a> e inicia sesion con la cuenta correspondiente.",
    },
    {
        "step": 2,
        "title": "Ve a Informes",
        "detail": "En el menu superior, haz clic en <strong>Informes</strong>.",
    },
    {
        "step": 3,
        "title": 'Haz clic en "Generar informe"',
        "detail": "Boton negro en la esquina superior derecha.",
    },
    {
        "step": 4,
        "title": "Selecciona el tipo de informe",
        "detail": 'En el desplegable "Tipo de notificacion", baja hasta el final '
                  'y selecciona <strong>Transaccion de pagos</strong>.',
    },
    {
        "step": 5,
        "title": "Selecciona las fechas",
        "detail": 'Haz clic en "Intervalo de tiempo", luego en la pestana '
                  "<strong>Rango personalizado</strong>. "
                  "Introduce la fecha de inicio y la fecha de fin.",
    },
    {
        "step": 6,
        "title": "Selecciona la organizacion",
        "detail": "Verifica que aparece la organizacion correcta "
                  "(solo hay una por cuenta).",
    },
    {
        "step": 7,
        "title": 'Pulsa "Generar"',
        "detail": "El informe tarda hasta <strong>3 minutos</strong> en generarse. "
                  "Volveras a la lista de Informes.",
    },
    {
        "step": 8,
        "title": "Descarga el CSV",
        "detail": 'Cuando aparezca el boton <strong>Descargar</strong> junto al '
                  "informe generado, haz clic para descargar el fichero CSV.",
    },
    {
        "step": 9,
        "title": "Sube el CSV",
        "detail": 'Ve al apartado <strong>Subir CSV</strong> de esta aplicacion, '
                  'selecciona plataforma <strong>Uber</strong> y sube el fichero descargado.',
    },
]
