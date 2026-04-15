"""Authentication routes: register and login."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from api.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from api.models import User
from api.rate_limit import auth_rate_limit
from api.repositories.user_repo import create_user, get_user_by_email
from api.schemas import (
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse)
@auth_rate_limit
async def register(
    request: Request,
    response: Response,
    body: RegisterRequest,
) -> RegisterResponse:
    """Register a new user account.

    Args:
        body: JSON with email and password fields.

    Returns:
        A dict containing the user id, email, and access token.

    Raises:
        HTTPException: 409 if the email is already registered.
    """
    existing = await get_user_by_email(body.email)
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
    await create_user(user)
    token = create_access_token(user.id)

    return RegisterResponse(
        id=user.id, email=user.email, token=token
    )


@router.post("/login", response_model=LoginResponse)
@auth_rate_limit
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> LoginResponse:
    """Authenticate and return an access token.

    Uses OAuth2 password form: username (email) + password.

    Args:
        form_data: OAuth2 form with username and password fields.

    Returns:
        A dict with access_token and token_type.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    user = await get_user_by_email(form_data.username)
    if user is None or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401, detail="Invalid credentials"
        )

    token = create_access_token(user.id)
    return LoginResponse(access_token=token, token_type="bearer")
