# tests/e2e/test_health.py
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
    from src.main import app
    return TestClient(app)


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_json(client):
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
