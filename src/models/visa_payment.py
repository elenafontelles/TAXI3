# src/models/visa_payment.py
import uuid
from datetime import datetime, date, time, timezone
from decimal import Decimal
from sqlalchemy import String, Date, Time, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class VisaPayment(Base):
    __tablename__ = "visa_payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    terminal_id: Mapped[str] = mapped_column(String(50), nullable=False)
    card_last4: Mapped[str] = mapped_column(String(20), nullable=False)
    brand: Mapped[str] = mapped_column(String(20), nullable=False)  # VISA, MASTERCARD
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    trip_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("trips.id"), nullable=True)
    tip_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
