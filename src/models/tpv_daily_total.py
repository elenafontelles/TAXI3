# src/models/tpv_daily_total.py
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class TpvDailyTotal(Base):
    __tablename__ = "tpv_daily_totals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=False)
    license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
