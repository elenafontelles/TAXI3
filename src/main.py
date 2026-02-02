# src/main.py
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.config import get_settings
from src.routes.auth import router as auth_router
from src.routes.dashboard import router as dashboard_router
from src.routes.trips import router as trips_router
from src.routes.summary import router as summary_router
from src.routes.export import router as export_router

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

# Static files - use absolute path so it works regardless of working directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(trips_router)
app.include_router(summary_router)
app.include_router(export_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "app": settings.APP_NAME}
