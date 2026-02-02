# src/routes/dashboard.py
import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.routes.auth import get_current_user
from src.database import get_session
from src.services.trip_service import get_earnings_summary

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, session: Session = Depends(get_session)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Drivers see only their own data
    driver_id = user["sub"] if user.get("role") == "driver" else None
    summary = get_earnings_summary(session, driver_id=driver_id)

    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "summary": summary,
    })
