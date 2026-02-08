# src/main.py
import os
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from src.config import get_settings
from src.routes.auth import router as auth_router, AuthRedirect
from src.routes.dashboard import router as dashboard_router
from src.routes.trips import router as trips_router
from src.routes.summary import router as summary_router
from src.routes.export import router as export_router
from src.routes.upload import router as upload_router
from src.routes.sync import router as sync_router
from src.routes.admin import router as admin_router
from src.routes.validation import router as validation_router
from src.routes.liquidacion import router as liquidacion_router
from src.routes.api_v1 import router as api_v1_router

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

# Static files - use absolute path so it works regardless of working directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Expose root_path to health endpoint
_root_path = os.environ.get("ROOT_PATH", "")

@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    """Reject cross-origin state-changing requests (CSRF defence)."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        origin = request.headers.get("origin") or request.headers.get("referer")
        if origin:
            allowed_host = request.headers.get("host", "").split(":")[0]
            request_host = urlparse(origin).hostname
            if request_host and request_host != allowed_host:
                return JSONResponse(status_code=403, content={"detail": "Origin not allowed"})
    return await call_next(request)


@app.exception_handler(AuthRedirect)
async def auth_redirect_handler(request: Request, exc: AuthRedirect):
    return RedirectResponse(url=exc.url, status_code=303)


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(trips_router)
app.include_router(summary_router)
app.include_router(export_router)
app.include_router(upload_router)
app.include_router(sync_router)
app.include_router(admin_router)
app.include_router(validation_router)
app.include_router(liquidacion_router)
app.include_router(api_v1_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "app": settings.APP_NAME, "root_path": _root_path}
