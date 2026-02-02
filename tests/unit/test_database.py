# tests/unit/test_database.py
def test_get_engine_returns_engine(monkeypatch):
    """get_engine should return a SQLAlchemy engine."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")

    from src.database import get_engine
    engine = get_engine()

    from sqlalchemy import Engine
    assert isinstance(engine, Engine)


def test_get_session_returns_session(monkeypatch):
    """get_session should yield a SQLAlchemy session."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")

    from src.database import get_session
    session_gen = get_session()
    session = next(session_gen)

    from sqlalchemy.orm import Session
    assert isinstance(session, Session)

    # Clean up
    session.close()
