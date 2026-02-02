# src/database.py
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from src.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.DATABASE_URL, echo=(settings.ENVIRONMENT == "development"))


def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
