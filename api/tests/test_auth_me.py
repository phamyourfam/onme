from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.auth import create_access_token
from api.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("api.main.settings.asset_storage_path", tmp_path)

    with (
        patch("api.main.init_models", new=AsyncMock()),
        patch("api.main.ping_database", new=AsyncMock()),
        patch("api.main.close_database", new=AsyncMock()),
    ):
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client


def test_auth_me_returns_current_user_profile(client: TestClient) -> None:
    now = datetime.now(timezone.utc).isoformat()
    user = SimpleNamespace(
        id="8b4a19b3-4f7d-43f1-af9f-f6a31234f6cf",
        email="hydrated@example.com",
        hashed_password="hashed-password",
        credits_remaining=7,
        last_credit_refresh=now,
        created_at=now,
    )
    token = create_access_token(user.id)

    with (
        patch("api.auth.get_user_by_id", new=AsyncMock(return_value=user)),
        patch("api.routes.auth.get_user_by_id", new=AsyncMock(return_value=user)),
    ):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "email": user.email,
        "credits_remaining": user.credits_remaining,
    }


def test_auth_me_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
