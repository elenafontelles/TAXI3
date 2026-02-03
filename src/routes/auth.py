# src/routes/auth.py
import time
from collections import defaultdict
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.database import get_session
from src.config import get_settings
from src.services.auth_service import verify_password, create_access_token, decode_access_token
from src.models.driver import Driver
from src.template_config import templates, root_path

router = APIRouter()

# Rate limiting: 5 attempts per IP per 5-minute window
_login_attempts: dict[str, list[float]] = defaultdict(list)
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300


def _is_rate_limited(ip: str) -> bool:
    now = time.monotonic()
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < _WINDOW_SECONDS]
    if len(_login_attempts[ip]) >= _MAX_ATTEMPTS:
        return True
    _login_attempts[ip].append(now)
    return False


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
async def login(request: Request, session: Session = Depends(get_session)):
    client_ip = request.client.host if request.client else "unknown"
    if _is_rate_limited(client_ip):
        return templates.TemplateResponse(
            request, "login.html",
            {"error": "Demasiados intentos. Espera unos minutos."},
        )

    form = await request.form()
    email = form.get("email")
    password = form.get("password")

    driver = session.query(Driver).filter(Driver.email == email).first()
    if not driver or not verify_password(password, driver.password_hash):
        return templates.TemplateResponse(request, "login.html", {"error": "Email o password incorrectos"})

    token = create_access_token({"sub": driver.id, "role": "admin" if driver.is_owner else "driver", "name": driver.name})
    response = RedirectResponse(url=f"{root_path}/", status_code=303)
    is_prod = get_settings().ENVIRONMENT != "development"
    response.set_cookie(
        key="access_token", value=token, httponly=True, max_age=86400,
        path="/", secure=is_prod, samesite="lax",
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url=f"{root_path}/login", status_code=303)
    response.delete_cookie("access_token", path="/")
    return response


def get_current_user(request: Request) -> dict | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    return decode_access_token(token)


class AuthRedirect(Exception):
    """Raised by auth dependencies to trigger a redirect."""
    def __init__(self, url: str):
        self.url = url


def require_auth(request: Request) -> dict:
    """FastAPI dependency: returns user dict or redirects to login."""
    user = get_current_user(request)
    if not user:
        raise AuthRedirect(f"{root_path}/login")
    return user


def require_admin(request: Request) -> dict:
    """FastAPI dependency: returns admin user dict or redirects."""
    user = require_auth(request)
    if user.get("role") not in ("admin", "owner"):
        raise AuthRedirect(f"{root_path}/")
    return user
