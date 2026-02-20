# src/models/trip.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(100), index=True)
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False, index=True)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=False, index=True)
    shift_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("shifts.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[float | None] = mapped_column(Numeric(10, 2))
    origin_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    origin_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    dest_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    dest_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    origin_address: Mapped[str | None] = mapped_column(Text)
    dest_address: Mapped[str | None] = mapped_column(Text)
    distance_km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    km_free: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency_code: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    gross_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    commission: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    platform_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    taxes_vat: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tips: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tolls: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    adjustments: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    payout_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    amount_breakdown: Mapped[dict | None] = mapped_column(JSON, default=dict)
    payment_method: Mapped[str | None] = mapped_column(String(20))
    fare_type: Mapped[str | None] = mapped_column(String(20))
    tariff_code: Mapped[str | None] = mapped_column(String(20))
    raw_data: Mapped[dict | None] = mapped_column(JSON)
    # Cross-platform linking: Prima trip (0 amount) -> FreeNow/Uber trip (with amount)
    linked_trip_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("trips.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
