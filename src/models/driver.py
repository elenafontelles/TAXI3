# src/models/driver.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("owners.id"), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    uber_driver_id: Mapped[str | None] = mapped_column(String(100))
    freenow_driver_id: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Commission configuration
    commission_base_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=40.0)
    commission_bonus_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=45.0)
    commission_threshold: Mapped[float] = mapped_column(Numeric(10, 2), default=300.0)
    freenow_commission_driver_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    uber_commission_driver_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
