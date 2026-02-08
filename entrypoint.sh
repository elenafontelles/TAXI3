#!/bin/bash
set -e

# If a custom command is passed (e.g. "arq ..."), run it directly
if [ $# -gt 0 ]; then
    echo "==> Running custom command: $@"
    exec "$@"
fi

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Starting server..."
exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --root-path "${ROOT_PATH:-}"
