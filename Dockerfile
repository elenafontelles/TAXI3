# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + Chromium deps
# (playwright install --with-deps fails on Debian Trixie due to Ubuntu-only package names)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    fonts-liberation \
    fonts-unifont \
    libasound2t64 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies + Chromium binary
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install chromium

# Copy source code
COPY src/ /app/src/
COPY scrapers/ /app/scrapers/
COPY scripts/ /app/scripts/
COPY migrations/ /app/migrations/
COPY alembic.ini /app/alembic.ini

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
