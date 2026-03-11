"""Unit tests for moodboard CRUD routes."""

import json
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


def _auth_headers(client, email="user@example.com"):
    """Register a user and return auth headers."""
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": "pass123"},
    )
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_moodboard(client):
    """Creating a moodboard returns id and title."""
    headers = _auth_headers(client)
    resp = client.post(
        "/moodboards/",
        json={"title": "My Board"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "My Board"
    assert "id" in body
    assert "created_at" in body


def test_list_excludes_canvas_state(client):
    """Listing moodboards does not include canvas_state."""
    headers = _auth_headers(client)
    client.post(
        "/moodboards/",
        json={"title": "Board A"},
        headers=headers,
    )
    resp = client.get("/moodboards/", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert "canvas_state" not in body[0]
    assert body[0]["title"] == "Board A"


def test_get_includes_canvas_state(client):
    """Getting a single moodboard includes canvas_state."""
    headers = _auth_headers(client)
    create_resp = client.post(
        "/moodboards/",
        json={"title": "Detailed"},
        headers=headers,
    )
    mb_id = create_resp.json()["id"]
    resp = client.get(f"/moodboards/{mb_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "canvas_state" in body
    assert body["title"] == "Detailed"


def test_update_canvas_state_persists(client):
    """Updating canvas state persists and round-trips."""
    headers = _auth_headers(client)
    create_resp = client.post(
        "/moodboards/",
        json={"title": "Canvas Test"},
        headers=headers,
    )
    mb_id = create_resp.json()["id"]
    canvas = json.dumps({"nodes": [{"id": "1", "x": 100, "y": 200}]})

    update_resp = client.put(
        f"/moodboards/{mb_id}/canvas",
        json={"canvas_state": canvas},
        headers=headers,
    )
    assert update_resp.status_code == 200

    get_resp = client.get(
        f"/moodboards/{mb_id}", headers=headers
    )
    assert get_resp.json()["canvas_state"] == canvas


def test_update_title(client):
    """Updating title persists."""
    headers = _auth_headers(client)
    create_resp = client.post(
        "/moodboards/", headers=headers
    )
    mb_id = create_resp.json()["id"]

    resp = client.put(
        f"/moodboards/{mb_id}/title",
        json={"title": "Renamed"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renamed"


def test_delete_owned_moodboard(client):
    """Deleting an owned moodboard returns 204."""
    headers = _auth_headers(client)
    create_resp = client.post(
        "/moodboards/",
        json={"title": "To Delete"},
        headers=headers,
    )
    mb_id = create_resp.json()["id"]

    resp = client.delete(
        f"/moodboards/{mb_id}", headers=headers
    )
    assert resp.status_code == 204

    # Verify it's gone
    get_resp = client.get(
        f"/moodboards/{mb_id}", headers=headers
    )
    assert get_resp.status_code == 404


def test_get_other_users_moodboard_403(client):
    """Accessing another user's moodboard returns 403."""
    headers_a = _auth_headers(client, "alice@example.com")
    headers_b = _auth_headers(client, "bob@example.com")

    create_resp = client.post(
        "/moodboards/",
        json={"title": "Alice's Board"},
        headers=headers_a,
    )
    mb_id = create_resp.json()["id"]

    # Bob tries to access Alice's board
    resp = client.get(
        f"/moodboards/{mb_id}", headers=headers_b
    )
    assert resp.status_code == 403
