from __future__ import annotations

import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import api.routes.tryon as tryon_routes
from api.auth import get_current_user
from api.main import app, build_cors_origins
from api.rate_limit import limiter


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


def test_build_cors_origins_allows_localhost_and_pages() -> None:
    assert build_cors_origins(
        [
            "http://localhost:5173",
            "https://preview.onme.pages.dev/",
        ]
    ) == [
        "http://localhost:5173",
        "https://preview.onme.pages.dev",
    ]


@pytest.mark.parametrize(
    ("origin", "message"),
    [
        ("https://*.pages.dev", "wildcard"),
        ("https://example.com", "Cloudflare Pages"),
    ],
)
def test_build_cors_origins_rejects_unsafe_origins(
    origin: str,
    message: str,
) -> None:
    with pytest.raises(RuntimeError, match=message):
        build_cors_origins([origin])


def test_auth_rate_limit_is_shared_across_register_and_login(
    client: TestClient,
) -> None:
    async def fake_get_user_by_email(email: str):
        if email == "login@example.com":
            return SimpleNamespace(
                id="user-1",
                email=email,
                hashed_password="hashed-password",
            )
        return None

    with (
        patch("api.routes.auth.get_user_by_email", new=fake_get_user_by_email),
        patch("api.routes.auth.create_user", new=AsyncMock()),
        patch("api.routes.auth.hash_password", return_value="hashed-password"),
        patch("api.routes.auth.verify_password", return_value=True),
        patch("api.routes.auth.create_access_token", return_value="token"),
    ):
        for index in range(3):
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"register-{index}@example.com",
                    "password": "strong-password",
                },
            )
            assert response.status_code == 200

        for _ in range(2):
            response = client.post(
                "/api/auth/login",
                data={
                    "username": "login@example.com",
                    "password": "strong-password",
                },
            )
            assert response.status_code == 200

        response = client.post(
            "/api/auth/login",
            data={
                "username": "login@example.com",
                "password": "strong-password",
            },
        )

    assert response.status_code == 429
    assert response.headers["Retry-After"]


def test_tryon_create_is_rate_limited_per_ip(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: "user-1"

    with (
        patch(
            "api.routes.tryon.check_and_refresh_credits",
            new=AsyncMock(return_value=9),
        ),
        patch("api.routes.tryon._repo.create_job", new=AsyncMock()),
        patch("api.routes.tryon.execute_tryon_job", new=lambda *_args, **_kwargs: None),
    ):
        for _ in range(5):
            response = client.post(
                "/api/tryon",
                files=_build_tryon_files(),
                data={"model_name": "catvton"},
            )
            assert response.status_code == 200

        response = client.post(
            "/api/tryon",
            files=_build_tryon_files(),
            data={"model_name": "catvton"},
        )

    assert response.status_code == 429
    assert response.headers["Retry-After"]
