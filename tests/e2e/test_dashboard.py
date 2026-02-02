# tests/e2e/test_dashboard.py
import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")

from src.services.auth_service import create_access_token


@pytest.fixture
def client():
    from src.main import app
    return TestClient(app)


@pytest.fixture
def auth_cookie():
    token = create_access_token({"sub": "user1", "role": "admin", "name": "Ivan"})
    return {"access_token": token}


def test_dashboard_requires_auth(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303


def test_dashboard_loads_for_authenticated_user(client, auth_cookie):
    response = client.get("/", cookies=auth_cookie)
    assert response.status_code == 200
    assert "TAXI API" in response.text
