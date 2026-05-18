# src/routes/download.py
"""Descargar CSVs - download files from platform portals."""
import asyncio
import logging
import os
from datetime import date, timedelta
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.routes.auth import require_admin
from src.database import get_session
from src.template_config import templates, root_path

logger = logging.getLogger(__name__)

router = APIRouter()

IMPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "imports"
)


def _list_import_files() -> list[dict]:
    """List CSV files available in the imports directory."""
    files = []
    if not os.path.isdir(IMPORTS_DIR):
        return files
    for name in sorted(os.listdir(IMPORTS_DIR), reverse=True):
        if not name.endswith(".csv"):
            continue
        path = os.path.join(IMPORTS_DIR, name)
        stat = os.stat(path)
        source = name.split("_")[0] if "_" in name else "unknown"
        files.append({
            "name": name,
            "source": source,
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": __import__("datetime").datetime.fromtimestamp(
                stat.st_mtime
            ).strftime("%d/%m/%Y %H:%M"),
        })
    return files


def _check_credentials(session: Session) -> dict:
    """Check which platform credentials are configured (DB or .env)."""
    from src.services.credential_service import get_credential
    return {
        "freenow_1": get_credential(session, "freenow", "account1") is not None,
        "freenow_2": get_credential(session, "freenow", "account2") is not None,
        "prima": get_credential(session, "prima", "") is not None,
    }


@router.get("/descargar-csvs", response_class=HTMLResponse)
async def download_page(
    request: Request,
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    creds = _check_credentials(session)
    import_files = _list_import_files()

    # Get result messages from query params (after redirect)
    success = request.query_params.get("success", "")
    error = request.query_params.get("error", "")

    # Uber instructions
    from scrapers.uber_scraper import UBER_DOWNLOAD_STEPS

    return templates.TemplateResponse(request, "descargar.html", {
        "user": user,
        "default_start": week_ago,
        "default_end": yesterday,
        "creds": creds,
        "import_files": import_files,
        "uber_steps": UBER_DOWNLOAD_STEPS,
        "success": success,
        "error": error,
    })


@router.post("/descargar-csvs/freenow", response_class=HTMLResponse)
async def download_freenow(
    request: Request,
    user: dict = Depends(require_admin),
    start_date: str = Form(""),
    end_date: str = Form(""),
    session: Session = Depends(get_session),
):
    """Download CSV from FreeNow account 1 (licenses 092 and 1061)."""
    return await _run_freenow_scraper("account1", start_date, end_date, session)


@router.post("/descargar-csvs/freenow-361", response_class=HTMLResponse)
async def download_freenow_361(
    request: Request,
    user: dict = Depends(require_admin),
    start_date: str = Form(""),
    end_date: str = Form(""),
    session: Session = Depends(get_session),
):
    """Download CSV from FreeNow account 2 (license 361)."""
    return await _run_freenow_scraper("account2", start_date, end_date, session)


async def _run_freenow_scraper(
    account_label: str, start_date: str, end_date: str, session: Session
) -> RedirectResponse:
    """Run FreeNow scraper synchronously and redirect with result."""
    from src.services.credential_service import get_credential
    cred = get_credential(session, "freenow", account_label)

    if not cred:
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=Credenciales de FreeNow ({account_label}) no configuradas",
            status_code=303,
        )

    yesterday = date.today() - timedelta(days=1)
    sd = date.fromisoformat(start_date) if start_date else yesterday
    ed = date.fromisoformat(end_date) if end_date else sd

    try:
        from scrapers.freenow_scraper import FreeNowScraper
        scraper = FreeNowScraper(
            start_date=sd, end_date=ed,
            email=cred["email"], password=cred["password"],
            account_label=account_label,
        )
        csv_path = await asyncio.to_thread(scraper.run)
    except Exception as e:
        logger.exception(f"FreeNow scraper failed: {e}")
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=Error descargando FreeNow: {e}",
            status_code=303,
        )

    if not csv_path:
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=No se pudo descargar el CSV de FreeNow (sin datos o credenciales incorrectas)",
            status_code=303,
        )

    filename = os.path.basename(csv_path)
    return RedirectResponse(
        url=f"{root_path}/descargar-csvs?success=FreeNow descargado: {filename}",
        status_code=303,
    )


@router.post("/descargar-csvs/prima", response_class=HTMLResponse)
async def download_prima(
    request: Request,
    user: dict = Depends(require_admin),
    start_date: str = Form(""),
    end_date: str = Form(""),
    session: Session = Depends(get_session),
):
    """Download CSV from Prima portal."""
    from src.services.credential_service import get_credential
    cred = get_credential(session, "prima", "")

    if not cred:
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=Credenciales de Prima no configuradas",
            status_code=303,
        )

    yesterday = date.today() - timedelta(days=1)
    sd = date.fromisoformat(start_date) if start_date else yesterday
    ed = date.fromisoformat(end_date) if end_date else sd

    try:
        from scrapers.prima_scraper import PrimaScraper
        scraper = PrimaScraper(start_date=sd, end_date=ed)
        csv_path = await asyncio.to_thread(scraper.run)
    except Exception as e:
        logger.exception(f"Prima scraper failed: {e}")
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=Error descargando Prima: {e}",
            status_code=303,
        )

    if not csv_path:
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=No se pudo descargar el CSV de Prima (sin datos o credenciales incorrectas)",
            status_code=303,
        )

    filename = os.path.basename(csv_path)
    return RedirectResponse(
        url=f"{root_path}/descargar-csvs?success=Prima descargado: {filename}",
        status_code=303,
    )


@router.get("/descargar-csvs/file/{filename}")
async def download_file_to_pc(
    filename: str,
    user: dict = Depends(require_admin),
):
    """Download a CSV file to the user's computer."""
    if "/" in filename or "\\" in filename or ".." in filename:
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=Nombre de archivo invalido",
            status_code=303,
        )

    filepath = os.path.join(IMPORTS_DIR, filename)
    if not os.path.isfile(filepath):
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=Archivo no encontrado: {filename}",
            status_code=303,
        )

    return FileResponse(
        filepath,
        filename=filename,
        media_type="text/csv",
    )


@router.post("/descargar-csvs/file/{filename}/upload", response_class=HTMLResponse)
async def upload_file_directly(
    filename: str,
    user: dict = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Shortcut: import a downloaded CSV directly (replace strategy)."""
    if "/" in filename or "\\" in filename or ".." in filename:
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=Nombre de archivo invalido",
            status_code=303,
        )

    filepath = os.path.join(IMPORTS_DIR, filename)
    if not os.path.isfile(filepath):
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=Archivo no encontrado: {filename}",
            status_code=303,
        )

    # Detect platform from filename
    name_lower = filename.lower()
    if "freenow" in name_lower:
        platform = "freenow"
    elif "prima" in name_lower:
        platform = "prima"
    elif "uber" in name_lower:
        platform = "uber"
    else:
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=No se pudo detectar la plataforma del archivo: {filename}",
            status_code=303,
        )

    try:
        from src.services.import_service import import_csv_file
        result = import_csv_file(filepath, platform, session)
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?success={result}",
            status_code=303,
        )
    except Exception as e:
        logger.exception(f"Import failed for {filename}: {e}")
        return RedirectResponse(
            url=f"{root_path}/descargar-csvs?error=Error importando {filename}: {e}",
            status_code=303,
        )


@router.post("/descargar-csvs/clear", response_class=HTMLResponse)
async def clear_downloads(
    request: Request,
    user: dict = Depends(require_admin),
):
    """Delete all downloaded files in imports/."""
    deleted = 0
    if os.path.isdir(IMPORTS_DIR):
        for name in os.listdir(IMPORTS_DIR):
            filepath = os.path.join(IMPORTS_DIR, name)
            if os.path.isfile(filepath):
                os.unlink(filepath)
                deleted += 1

    return RedirectResponse(
        url=f"{root_path}/descargar-csvs?success=Eliminados {deleted} archivos",
        status_code=303,
    )
