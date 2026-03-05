# src/models/freenow_adjustment.py
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class FreenowAdjustment(Base):
    __tablename__ = "freenow_adjustments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    adjustment_type: Mapped[str] = mapped_column(String(20), nullable=False)  # otros, incentivos
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
