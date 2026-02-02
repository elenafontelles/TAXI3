# tests/e2e/test_sync.py
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
def admin_cookie():
    token = create_access_token({"sub": "user1", "role": "admin", "name": "Ivan"})
    return {"access_token": token}


@pytest.fixture
def driver_cookie():
    token = create_access_token({"sub": "user2", "role": "driver", "name": "Carlos"})
    return {"access_token": token}


def test_sync_requires_auth(client):
    response = client.get("/sync", follow_redirects=False)
    assert response.status_code == 303


def test_sync_loads_for_admin(client, admin_cookie):
    response = client.get("/sync", cookies=admin_cookie)
    assert response.status_code == 200
    assert "Sincronizacion" in response.text


def test_sync_redirects_driver(client, driver_cookie):
    response = client.get("/sync", cookies=driver_cookie, follow_redirects=False)
    assert response.status_code == 303
