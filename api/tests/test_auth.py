"""Unit tests for api.auth module."""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from api.auth import (
    check_and_refresh_credits,
    create_access_token,
    hash_password,
    verify_password,
)
from api.database import init_db
from api.models import User
from api.repositories.user_repo import create_user, get_user_by_id


@pytest.fixture(autouse=True)
def _tmp_database(tmp_path):
    """Redirect the database to a temporary directory for each test."""
    db_path = str(tmp_path / "test.db")
    with patch("api.database.settings") as mock_settings:
        mock_settings.DATABASE_PATH = db_path
        init_db()
        yield


def _make_user(**overrides) -> User:
    """Create a test user with sensible defaults."""
    defaults = {
        "id": "user-1",
        "email": "test@example.com",
        "hashed_password": hash_password("secret"),
        "credits_remaining": 10,
        "last_credit_refresh": datetime.now(
            timezone.utc
        ).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    defaults.update(overrides)
    return User(**defaults)


def test_hash_and_verify_correct_password():
    """Correct password verification returns True."""
    hashed = hash_password("my-password")
    assert verify_password("my-password", hashed) is True


def test_verify_rejects_wrong_password():
    """Wrong password verification returns False."""
    hashed = hash_password("my-password")
    assert verify_password("wrong-password", hashed) is False


def test_create_and_decode_token():
    """Token round-trips through create and decode."""
    from jose import jwt

    from api.config import settings

    token = create_access_token("user-42")
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=["HS256"]
    )
    assert payload["sub"] == "user-42"
    assert "exp" in payload


def test_credits_deduct_from_ten_to_nine():
    """Using a credit decrements from 10 to 9."""
    user = _make_user()
    create_user(user)
    remaining = check_and_refresh_credits("user-1")
    assert remaining == 9

    fetched = get_user_by_id("user-1")
    assert fetched is not None
    assert fetched.credits_remaining == 9


def test_credits_refresh_after_midnight():
    """Credits reset to 10 when last refresh was yesterday."""
    yesterday = (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).isoformat()
    user = _make_user(
        credits_remaining=0,
        last_credit_refresh=yesterday,
    )
    create_user(user)
    remaining = check_and_refresh_credits("user-1")
    # After refresh (10) then decrement (9)
    assert remaining == 9


def test_credits_raise_429_when_zero_today():
    """Zero credits today raises 429."""
    now = datetime.now(timezone.utc).isoformat()
    user = _make_user(
        credits_remaining=0,
        last_credit_refresh=now,
    )
    create_user(user)
    with pytest.raises(Exception) as exc_info:
        check_and_refresh_credits("user-1")
    assert exc_info.value.status_code == 429
