# tests/e2e/test_auth.py
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
    from src.main import app
    return TestClient(app)


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Email" in response.text
    assert "Password" in response.text


def test_unauthenticated_redirect(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in [302, 303, 307]
