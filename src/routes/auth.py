# src/routes/auth.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.database import get_session
from src.config import get_settings
from src.services.auth_service import verify_password, create_access_token, decode_access_token
from src.models.driver import Driver
from src.template_config import templates, root_path

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
async def login(request: Request, session: Session = Depends(get_session)):
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
