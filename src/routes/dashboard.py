# src/routes/dashboard.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from src.routes.auth import require_auth
from src.database import get_session
from src.services.trip_service import get_earnings_summary
from src.template_config import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(require_auth), session: Session = Depends(get_session)):
    driver_id = user["sub"] if user.get("role") == "driver" else None
    summary = get_earnings_summary(session, driver_id=driver_id)
    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "summary": summary,
    })
