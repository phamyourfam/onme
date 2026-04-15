"""Moodboard persistence backed by PostgreSQL via SQLAlchemy."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update

from api.database import AsyncSessionFactory
from api.db.models import MoodboardORM
from api.models import Moodboard


def _as_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _decode_canvas(canvas_state: str | None) -> dict[str, object]:
    if not canvas_state:
        return {}
    return json.loads(canvas_state)


def _encode_canvas(canvas_state: dict[str, object] | None) -> str | None:
    if canvas_state is None:
        return None
    return json.dumps(canvas_state)


def _to_moodboard(model: MoodboardORM) -> Moodboard:
    return Moodboard(
        id=model.id.hex,
        user_id=model.user_id.hex,
        title=model.title,
        canvas_state=_encode_canvas(model.canvas_state),
        created_at=model.created_at.isoformat(),
        updated_at=model.updated_at.isoformat(),
    )


async def create_moodboard(moodboard: Moodboard) -> Moodboard:
    async with AsyncSessionFactory() as session:
        model = MoodboardORM(
            id=_as_uuid(moodboard.id),
            user_id=_as_uuid(moodboard.user_id),
            title=moodboard.title,
            canvas_state=_decode_canvas(moodboard.canvas_state),
            created_at=_to_datetime(moodboard.created_at),
            updated_at=_to_datetime(moodboard.updated_at),
        )
        session.add(model)
        await session.commit()
    return moodboard


async def get_moodboard(moodboard_id: str) -> Moodboard | None:
    async with AsyncSessionFactory() as session:
        model = await session.get(MoodboardORM, _as_uuid(moodboard_id))
    if model is None:
        return None
    return _to_moodboard(model)


async def list_user_moodboards(user_id: str) -> list[Moodboard]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(MoodboardORM)
            .where(MoodboardORM.user_id == _as_uuid(user_id))
            .order_by(MoodboardORM.updated_at.desc())
        )
        models = result.scalars().all()
    return [_to_moodboard(model) for model in models]


async def update_moodboard_canvas(
    moodboard_id: str, canvas_state: str, updated_at: str
) -> None:
    async with AsyncSessionFactory() as session:
        await session.execute(
            update(MoodboardORM)
            .where(MoodboardORM.id == _as_uuid(moodboard_id))
            .values(
                canvas_state=_decode_canvas(canvas_state),
                updated_at=_to_datetime(updated_at),
            )
        )
        await session.commit()


async def update_moodboard_title(
    moodboard_id: str, title: str, updated_at: str
) -> None:
    async with AsyncSessionFactory() as session:
        await session.execute(
            update(MoodboardORM)
            .where(MoodboardORM.id == _as_uuid(moodboard_id))
            .values(title=title, updated_at=_to_datetime(updated_at))
        )
        await session.commit()


async def delete_moodboard(moodboard_id: str, user_id: str) -> bool:
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            delete(MoodboardORM).where(
                MoodboardORM.id == _as_uuid(moodboard_id),
                MoodboardORM.user_id == _as_uuid(user_id),
            )
        )
        await session.commit()
    return result.rowcount > 0
