# src/models/fuel_expense.py
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class FuelExpense(Base):
    __tablename__ = "fuel_expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=False)
    driver_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=True)
    liters: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # petroprix, repsol
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)  # efectivo, tarjeta
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
