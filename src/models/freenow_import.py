# src/models/freenow_import.py
import uuid
from datetime import datetime, date as date_type, timezone
from sqlalchemy import String, Integer, BigInteger, Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class FreeNowImport(Base):
    __tablename__ = "freenow_imports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    import_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    records_imported: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
