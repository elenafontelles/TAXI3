# src/main.py
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from src.config import get_settings
from src.routes.auth import router as auth_router, get_current_user

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

# Static files - use absolute path so it works regardless of working directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "app": settings.APP_NAME}


@app.get("/")
async def home(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return {"message": f"Welcome {user['name']}"}
