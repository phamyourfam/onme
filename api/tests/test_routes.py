"""Unit tests for the API route endpoints."""

import io
import os
import tempfile
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
        yield {"upload_dir": upload_dir, "results_dir": results_dir}


@pytest.fixture()
def client(_dirs):
    """Create a TestClient with patched settings."""
    from api.main import app

    # Re-mount static files with temp directories
    # The app already has routes registered; just use TestClient
    return TestClient(app, raise_server_exceptions=False)


# ── Health ──────────────────────────────────────────────────────────


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


# ── Upload ──────────────────────────────────────────────────────────


def test_upload_success(client):
    person = ("person.jpg", io.BytesIO(b"\xff\xd8fake-person"), "image/jpeg")
    garment = ("garment.jpg", io.BytesIO(b"\xff\xd8fake-garment"), "image/jpeg")
    resp = client.post(
        "/tryon",
        files={"person": person, "garment": garment},
        data={"model_name": "catvton"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["model_name"] == "catvton"
    assert body["id"]  # non-empty


def test_upload_rejects_missing_person(client):
    garment = ("garment.jpg", io.BytesIO(b"\xff\xd8fake"), "image/jpeg")
    resp = client.post(
        "/tryon",
        files={"garment": garment},
        data={"model_name": "catvton"},
    )
    assert resp.status_code == 422


def test_upload_rejects_missing_model_name(client):
    person = ("person.jpg", io.BytesIO(b"\xff\xd8fake"), "image/jpeg")
    garment = ("garment.jpg", io.BytesIO(b"\xff\xd8fake"), "image/jpeg")
    resp = client.post(
        "/tryon",
        files={"person": person, "garment": garment},
    )
    assert resp.status_code == 422


# ── GET job status ──────────────────────────────────────────────────


def test_get_job_success(client):
    # First create a job
    person = ("person.jpg", io.BytesIO(b"\xff\xd8fake-person"), "image/jpeg")
    garment = ("garment.jpg", io.BytesIO(b"\xff\xd8fake-garment"), "image/jpeg")
    create_resp = client.post(
        "/tryon",
        files={"person": person, "garment": garment},
        data={"model_name": "catvton"},
    )
    job_id = create_resp.json()["id"]

    # Now fetch it
    resp = client.get(f"/tryon/{job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == job_id
    assert body["status"] == "pending"


def test_get_job_404(client):
    resp = client.get("/tryon/nonexistent-id")
    assert resp.status_code == 404
