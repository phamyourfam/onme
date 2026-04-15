"""User persistence backed by PostgreSQL via SQLAlchemy."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update

from api.database import AsyncSessionFactory
from api.db.models import UserORM
from api.models import User


def _as_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_user(model: UserORM) -> User:
    return User(
        id=model.id.hex,
        email=model.email,
        hashed_password=model.hashed_password,
        credits_remaining=model.credits_remaining,
        last_credit_refresh=model.last_credit_refresh.isoformat(),
        created_at=model.created_at.isoformat(),
    )


def _to_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


async def create_user(user: User) -> User:
    async with AsyncSessionFactory() as session:
        model = UserORM(
            id=_as_uuid(user.id),
            email=user.email,
            hashed_password=user.hashed_password,
            credits_remaining=user.credits_remaining,
            last_credit_refresh=_to_datetime(user.last_credit_refresh),
            created_at=_to_datetime(user.created_at),
        )
        session.add(model)
        await session.commit()
    return user


async def get_user_by_email(email: str) -> User | None:
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(UserORM).where(UserORM.email == email)
        )
        model = result.scalar_one_or_none()
    if model is None:
        return None
    return _to_user(model)


async def get_user_by_id(user_id: str) -> User | None:
    async with AsyncSessionFactory() as session:
        model = await session.get(UserORM, _as_uuid(user_id))
    if model is None:
        return None
    return _to_user(model)


async def update_user_credits(
    user_id: str, credits: int, refresh_time: str
) -> None:
    async with AsyncSessionFactory() as session:
        await session.execute(
            update(UserORM)
            .where(UserORM.id == _as_uuid(user_id))
            .values(
                credits_remaining=credits,
                last_credit_refresh=_to_datetime(refresh_time),
            )
        )
        await session.commit()
