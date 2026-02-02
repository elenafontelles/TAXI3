#!/bin/bash
# Nightly sync: run scrapers then import CSVs
# Triggered by cron at 02:00 AM daily

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "$(date): Starting nightly sync..."

# Run scrapers sequentially
ERRORS=""

echo "Running Uber scraper..."
python scrapers/uber_scraper.py || ERRORS="${ERRORS}Uber scraper failed. "

echo "Running FreeNow scraper..."
python scrapers/freenow_scraper.py || ERRORS="${ERRORS}FreeNow scraper failed. "

echo "Running Prima scraper..."
python scrapers/prima_scraper.py || ERRORS="${ERRORS}Prima scraper failed. "

# Import CSVs even if some scrapers failed
echo "Importing CSV files..."
python -c "
from sqlalchemy.orm import Session
from src.database import get_engine
from sqlalchemy.orm import sessionmaker
from scripts.import_csvs import import_csv_files

engine = get_engine()
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
try:
    result = import_csv_files('imports', session)
    print(f'Import complete: {result}')
finally:
    session.close()
" || ERRORS="${ERRORS}CSV import failed. "

# Send alert if there were errors
if [ -n "$ERRORS" ]; then
    echo "Errors occurred: $ERRORS"
    python -c "
from scripts.send_email import send_alert
send_alert('Nightly Sync Errors', '$ERRORS')
"
fi

echo "$(date): Nightly sync complete."
