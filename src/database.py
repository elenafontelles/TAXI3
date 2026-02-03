# src/database.py
from functools import lru_cache
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from src.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        echo=(settings.ENVIRONMENT == "development"),
        pool_pre_ping=True,
    )


@lru_cache
def _get_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=get_engine())


def get_session():
    session = _get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()
