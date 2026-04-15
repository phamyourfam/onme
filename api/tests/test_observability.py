from __future__ import annotations

import io
import json
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

import api.routes.tryon as tryon_routes
from api.auth import get_current_user
from api.logging_config import configure_logging
from api.main import app
from api.rate_limit import limiter
from api.services.inference import run_inference_sync
from loguru import logger


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("api.main.settings.asset_storage_path", tmp_path)
    monkeypatch.setattr(tryon_routes.settings, "asset_storage_path", tmp_path)
    limiter.reset()

    with (
        patch("api.main.init_models", new=AsyncMock()),
        patch("api.main.ping_database", new=AsyncMock()),
        patch("api.main.close_database", new=AsyncMock()),
    ):
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client

    app.dependency_overrides.clear()
    limiter.reset()


def _build_tryon_files() -> dict[str, tuple[str, io.BytesIO, str]]:
    return {
        "person": ("person.jpg", io.BytesIO(b"\xff\xd8person"), "image/jpeg"),
        "garment": ("garment.jpg", io.BytesIO(b"\xff\xd8garment"), "image/jpeg"),
    }


def test_json_formatter_serializes_event_fields() -> None:
    # Test our custom loguru JSON sink
    from api.logging_config import _json_sink
    
    output = io.StringIO()
    with patch("sys.stderr", output):
        logger.remove()
        logger.add(_json_sink, serialize=False)
        
        test_logger = logger.bind(user_id="user-1", job_id="job-1", name="onme.api.tryon")
        test_logger.info("tryon_job_queued")

    payload = json.loads(output.getvalue())

    assert payload["event"] == "tryon_job_queued"
    assert payload["level"] == "info"
    # Note: custom loguru sink uses bound 'name' attribute in 'extra' if we bind it, 
    # but the native record name is the module name (e.g. test_observability).
    # Since we test _json_sink directly, we check for event and level and bound extra params
    assert payload["extra"]["user_id"] == "user-1"
    assert payload["extra"]["job_id"] == "job-1"
    assert "timestamp" in payload


def test_create_tryon_logs_job_queued(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: "user-1"
    caplog.set_level(logging.INFO)

    with (
        patch(
            "api.routes.tryon.check_and_refresh_credits",
            new=AsyncMock(return_value=9),
        ),
        patch("api.routes.tryon._repo.create_job", new=AsyncMock()),
        patch("api.routes.tryon.execute_tryon_job", new=lambda *_args, **_kwargs: None),
    ):
        response = client.post(
            "/api/tryon",
            files=_build_tryon_files(),
            data={"model_name": "catvton"},
        )

    assert response.status_code == 200
    job_id = response.json()["id"]

    record = next(
        entry for entry in caplog.records if entry.msg == "tryon_job_queued"
    )
    assert record.user_id == "user-1"
    assert record.job_id == job_id
    assert record.model_name == "catvton"


def test_run_inference_sync_logs_replicate_success(
    tmp_path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    person_path = tmp_path / "person.jpg"
    garment_path = tmp_path / "garment.jpg"
    person_path.write_bytes(b"person")
    garment_path.write_bytes(b"garment")

    fake_client = Mock()
    fake_client.run.return_value = ["https://example.com/result.jpg"]
    caplog.set_level(logging.INFO)

    with patch("api.services.inference.replicate.Client", return_value=fake_client):
        output_url = run_inference_sync(
            job_id="job-1",
            model_name="catvton",
            person_image_path=str(person_path),
            garment_image_path=str(garment_path),
        )

    assert output_url == "https://example.com/result.jpg"

    events = [
        entry for entry in caplog.records if entry.name == "onme.api.inference"
    ]
    assert [entry.msg for entry in events] == [
        "replicate_api_called",
        "replicate_api_responded",
    ]
    assert events[0].job_id == "job-1"
    assert events[0].model_name == "catvton"
    assert events[1].outcome == "success"


def test_run_inference_sync_logs_replicate_failure(
    tmp_path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    person_path = tmp_path / "person.jpg"
    garment_path = tmp_path / "garment.jpg"
    person_path.write_bytes(b"person")
    garment_path.write_bytes(b"garment")

    fake_client = Mock()
    fake_client.run.side_effect = RuntimeError("replicate unavailable")
    caplog.set_level(logging.INFO)

    with (
        patch("api.services.inference.replicate.Client", return_value=fake_client),
        pytest.raises(RuntimeError, match="replicate unavailable"),
    ):
        run_inference_sync(
            job_id="job-1",
            model_name="catvton",
            person_image_path=str(person_path),
            garment_image_path=str(garment_path),
        )

    events = [
        entry for entry in caplog.records if entry.name == "onme.api.inference"
    ]
    assert [entry.msg for entry in events] == [
        "replicate_api_called",
        "replicate_api_responded",
    ]
    assert events[1].outcome == "failure"
    assert events[1].error == "replicate unavailable"
