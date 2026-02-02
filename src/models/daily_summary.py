# src/models/daily_summary.py
import uuid
from datetime import datetime, date as date_type, timezone
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    driver_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("drivers.id"))
    vehicle_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("vehicles.id"))
    trips_uber: Mapped[int] = mapped_column(Integer, default=0)
    trips_freenow: Mapped[int] = mapped_column(Integer, default=0)
    trips_prima: Mapped[int] = mapped_column(Integer, default=0)
    trips_street: Mapped[int] = mapped_column(Integer, default=0)
    total_trips: Mapped[int] = mapped_column(Integer, default=0)
    total_km: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_gross: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_commission: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_net: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    avg_trip_value: Mapped[float | None] = mapped_column(Numeric(10, 2))
    euro_per_km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("date", "driver_id", "vehicle_id"),)
