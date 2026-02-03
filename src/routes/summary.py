# src/routes/summary.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from src.routes.auth import require_admin
from src.template_config import templates

router = APIRouter()


@router.get("/summary", response_class=HTMLResponse)
async def summary_page(request: Request, user: dict = Depends(require_admin)):
    return templates.TemplateResponse(request, "summary.html", {"user": user, "summaries": []})
