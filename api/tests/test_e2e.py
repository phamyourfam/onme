"""End-to-end smoke tests for the OnMe virtual try-on API."""

import io
import os
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image


def _make_jpeg(width: int = 512, height: int = 512) -> io.BytesIO:
    """Create a synthetic JPEG image in memory."""
    img = Image.new("RGB", (width, height), color=(128, 128, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


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

    return TestClient(app, raise_server_exceptions=False)


# ── Test 1: Upload and Poll ────────────────────────────────────────


def test_upload_and_poll(client):
    """POST two images, then GET the job by ID to verify the upload-to-poll flow."""
    person_buf = _make_jpeg()
    garment_buf = _make_jpeg()

    resp = client.post(
        "/tryon",
        files={
            "person": ("person.jpg", person_buf, "image/jpeg"),
            "garment": ("garment.jpg", garment_buf, "image/jpeg"),
        },
        data={"model_name": "catvton"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["id"] is not None

    job_id = body["id"]

    poll_resp = client.get(f"/tryon/{job_id}")
    assert poll_resp.status_code == 200
    poll_body = poll_resp.json()
    assert poll_body["id"] == job_id


# ── Test 2: Reject Invalid Inputs ──────────────────────────────────


def test_rejects_invalid_inputs(client):
    """Verify the API rejects bad content types, invalid model names, and missing jobs."""
    person_buf = _make_jpeg()
    garment_buf = _make_jpeg()

    # POST with a text file instead of an image
    text_file = io.BytesIO(b"this is not an image")
    resp = client.post(
        "/tryon",
        files={
            "person": ("notes.txt", text_file, "text/plain"),
            "garment": ("garment.jpg", garment_buf, "image/jpeg"),
        },
        data={"model_name": "catvton"},
    )
    assert resp.status_code == 400

    # POST with an invalid model_name
    person_buf.seek(0)
    garment_buf.seek(0)
    resp = client.post(
        "/tryon",
        files={
            "person": ("person.jpg", person_buf, "image/jpeg"),
            "garment": ("garment.jpg", garment_buf, "image/jpeg"),
        },
        data={"model_name": "nonexistent_model"},
    )
    assert resp.status_code == 400

    # GET a nonexistent job
    resp = client.get("/tryon/nonexistent_id")
    assert resp.status_code == 404


# ── Test 3: Full Pipeline with Replicate ───────────────────────────


@pytest.mark.skipif(
    not os.environ.get("REPLICATE_API_TOKEN"),
    reason="Requires REPLICATE_API_TOKEN",
)
def test_full_pipeline_with_replicate(tmp_path):
    """Run the full pipeline end-to-end against the real Replicate API."""
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
    ):
        from api.database import init_db

        init_db()

        from api.main import app

        client = TestClient(app, raise_server_exceptions=False)

        person_buf = _make_jpeg()
        garment_buf = _make_jpeg()

        resp = client.post(
            "/tryon",
            files={
                "person": ("person.jpg", person_buf, "image/jpeg"),
                "garment": ("garment.jpg", garment_buf, "image/jpeg"),
            },
            data={"model_name": "catvton"},
        )
        assert resp.status_code == 200
        job_id = resp.json()["id"]

        max_polls = 40
        poll_interval = 3

        for _ in range(max_polls):
            time.sleep(poll_interval)
            poll_resp = client.get(f"/tryon/{job_id}")
            assert poll_resp.status_code == 200
            poll_body = poll_resp.json()

            if poll_body["status"] == "complete":
                assert poll_body["result_url"] is not None
                assert "person_clahe" in poll_body["intermediates"]
                assert "colour_corrected" in poll_body["intermediates"]
                assert poll_body["timing"] is not None
                return

            if poll_body["status"] == "failed":
                pytest.fail(
                    f"Pipeline failed: {poll_body.get('error_message', 'unknown error')}"
                )

        pytest.fail(
            f"Pipeline did not complete after {max_polls * poll_interval}s of polling"
        )
