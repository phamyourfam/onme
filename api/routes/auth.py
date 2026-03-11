"""Authentication routes: register and login."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from pydantic import BaseModel

from api.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from api.models import User
from api.repositories.user_repo import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


class _RegisterBody(BaseModel):
    """JSON body for user registration."""

    email: str
    password: str


@router.post("/register")
def register(body: _RegisterBody) -> dict:
    """Register a new user account.

    Args:
        body: JSON with email and password fields.

    Returns:
        A dict containing the user id, email, and access token.

    Raises:
        HTTPException: 409 if the email is already registered.
    """
    existing = get_user_by_email(body.email)
    if existing is not None:
        raise HTTPException(
            status_code=409, detail="Email already registered"
        )

    now = datetime.now(timezone.utc).isoformat()
    user = User(
        id=uuid.uuid4().hex,
        email=body.email,
        hashed_password=hash_password(body.password),
        credits_remaining=10,
        last_credit_refresh=now,
        created_at=now,
    )
    create_user(user)
    token = create_access_token(user.id)

    return {"id": user.id, "email": user.email, "token": token}


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict:
    """Authenticate and return an access token.

    Uses OAuth2 password form: username (email) + password.

    Args:
        form_data: OAuth2 form with username and password fields.

    Returns:
        A dict with access_token and token_type.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    user = get_user_by_email(form_data.username)
    if user is None or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401, detail="Invalid credentials"
        )

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
