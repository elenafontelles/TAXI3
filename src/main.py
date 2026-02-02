# src/main.py
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

# Static files - use absolute path so it works regardless of working directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "app": settings.APP_NAME}
