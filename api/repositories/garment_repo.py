"""Garment persistence backed by PostgreSQL via SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import select

from api.database import AsyncSessionFactory
from api.db.models import GarmentORM
from api.models import Garment


def _to_garment(model: GarmentORM) -> Garment:
    return Garment(
        id=model.id,
        image_path=model.image_path,
        category=model.category,
        display_name=model.display_name,
        source_credit=model.source_credit,
    )


async def list_garments(category: str | None = None) -> list[Garment]:
    async with AsyncSessionFactory() as session:
        statement = select(GarmentORM)
        if category:
            statement = statement.where(GarmentORM.category == category.lower())
        result = await session.execute(statement.order_by(GarmentORM.display_name))
        models = result.scalars().all()
    return [_to_garment(model) for model in models]


async def get_garment(garment_id: str) -> Garment | None:
    async with AsyncSessionFactory() as session:
        model = await session.get(GarmentORM, garment_id)
    if model is None:
        return None
    return _to_garment(model)
