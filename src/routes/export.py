# src/routes/export.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from src.routes.auth import get_current_user
from src.template_config import templates, root_path

router = APIRouter()


@router.get("/export", response_class=HTMLResponse)
async def export_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url=f"{root_path}/login", status_code=303)
    if user.get("role") not in ("admin", "owner"):
        return RedirectResponse(url=f"{root_path}/", status_code=303)
    return templates.TemplateResponse(request, "export.html", {"user": user})
