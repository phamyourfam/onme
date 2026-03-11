"""Unit tests for auth route endpoints (register/login)."""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def _dirs(tmp_path):
    """Patch settings to use temp directories and initialise the database."""
    upload_dir = str(tmp_path / "uploads")
    results_dir = str(tmp_path / "results")
    db_path = str(tmp_path / "test.db")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    with (
        patch("api.config.settings.UPLOAD_DIR", upload_dir),
        patch("api.config.settings.RESULTS_DIR", results_dir),
        patch("api.config.settings.DATABASE_PATH", db_path),
        patch("api.database.settings.DATABASE_PATH", db_path),
        patch("api.routes.tryon.settings.UPLOAD_DIR", upload_dir),
        patch("api.routes.tryon.execute_tryon_job", lambda *a, **kw: None),
    ):
        from api.database import init_db

        init_db()
        yield


@pytest.fixture()
def client(_dirs):
    """Create a TestClient with patched settings."""
    from api.main import app

    return TestClient(app, raise_server_exceptions=False)


def test_register_success(client):
    """Successful registration returns id, email, and token."""
    resp = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "pass123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "id" in body
    assert "token" in body


def test_register_duplicate_409(client):
    """Registering the same email twice returns 409."""
    client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "pass123"},
    )
    resp = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "pass456"},
    )
    assert resp.status_code == 409


def test_login_success(client):
    """Login with correct credentials returns access_token."""
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "pass123"},
    )
    resp = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "pass123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_401(client):
    """Login with wrong password returns 401."""
    client.post(
        "/auth/register",
        json={"email": "wrongpw@example.com", "password": "pass123"},
    )
    resp = client.post(
        "/auth/login",
        data={
            "username": "wrongpw@example.com",
            "password": "wrong",
        },
    )
    assert resp.status_code == 401
