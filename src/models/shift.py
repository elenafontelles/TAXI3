# src/models/shift.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    km_free: Mapped[float | None] = mapped_column(Numeric(10, 2))
    km_occupied: Mapped[float | None] = mapped_column(Numeric(10, 2))
    max_speed: Mapped[float | None] = mapped_column(Numeric(5, 1))
    total_earnings: Mapped[float | None] = mapped_column(Numeric(10, 2))
    raw_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
