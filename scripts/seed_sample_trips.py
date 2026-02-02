"""Generate sample trip data for testing the dashboard."""
import os
import sys
import random
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models.trip import Trip
import src.models  # noqa

DRIVERS = [
    ("a330b35c-8e93-418d-9196-40c80a1468b4", "794f51c7-e4d6-4190-8ce9-18f30f52e15a"),  # Ivan + 1234-ABC
    ("81d56f84-097c-4452-a714-43a88e907f8f", "794f51c7-e4d6-4190-8ce9-18f30f52e15a"),  # Carlos + 1234-ABC
    ("3c7e7d78-143b-470f-9e36-e590e4dbbe92", "f21ed6c7-9bff-47a5-8ca0-bb1ba7c8ee90"),  # Maria + 5678-DEF
    ("fa8eb94e-1567-4f48-bbd3-c270a3e17f3b", "0fb60f3d-0eab-421b-886e-68e3788d746c"),  # Pedro + 9012-GHI
    ("3ac748ff-0aed-4a64-b7da-5c1a18f5cb04", "0fb60f3d-0eab-421b-886e-68e3788d746c"),  # Elena + 9012-GHI
]

SOURCES = ["uber", "freenow", "prima"]

def generate_trips():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    now = datetime(2026, 2, 2, 20, 0, tzinfo=timezone.utc)
    trips = []

    for day_offset in range(7):
        date = now - timedelta(days=day_offset)
        # 6-10 trips per day
        num_trips = random.randint(6, 10)
        for i in range(num_trips):
            driver_id, vehicle_id = random.choice(DRIVERS)
            source = random.choice(SOURCES)
            hour = random.randint(6, 22)
            minute = random.randint(0, 59)
            started_at = date.replace(hour=hour, minute=minute)

            gross = round(random.uniform(8, 45), 2)
            commission_rate = 0.20 if source == "uber" else 0.15 if source == "freenow" else 0.0
            commission = round(gross * commission_rate, 2)
            tips = round(random.uniform(0, 5), 2) if random.random() > 0.5 else 0
            payout = round(gross - commission + tips, 2)
            distance = round(random.uniform(1.5, 15.0), 1)

            trip = Trip(
                source=source,
                external_id=f"{source}_{date.strftime('%Y%m%d')}_{i:03d}",
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                started_at=started_at,
                gross_amount=gross,
                commission=commission,
                tips=tips,
                payout_amount=payout,
                distance_km=distance,
                payment_method=random.choice(["card", "cash"]),
                currency_code="EUR",
            )
            trips.append(trip)

    session.add_all(trips)
    session.commit()
    print(f"Created {len(trips)} sample trips")

    # Show summary
    from sqlalchemy import func
    total = session.query(func.sum(Trip.gross_amount)).scalar()
    print(f"Total gross: {total:.2f} EUR")
    session.close()

if __name__ == "__main__":
    random.seed(42)  # Reproducible
    generate_trips()
