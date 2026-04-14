"""Seed the garment catalog in PostgreSQL."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy.dialects.postgresql import insert

from api.database import AsyncSessionFactory, init_models
from api.db.models import GarmentORM

GARMENTS = [
    ("Classic White T-Shirt", "tops", None),
    ("Navy Striped Polo", "tops", None),
    ("Black Crew Neck Tee", "tops", None),
    ("Linen Button-Down Shirt", "tops", None),
    ("Heather Grey Henley", "tops", None),
    ("Chambray Camp Collar Shirt", "tops", None),
    ("Ribbed Tank Top", "tops", None),
    ("Slim Fit Dark Wash Jeans", "bottoms", None),
    ("Khaki Chinos", "bottoms", None),
    ("Black Tailored Trousers", "bottoms", None),
    ("Olive Cargo Pants", "bottoms", None),
    ("Light Wash Relaxed Jeans", "bottoms", None),
    ("Navy Linen Shorts", "bottoms", None),
    ("Grey Jogger Pants", "bottoms", None),
    ("Floral Midi Wrap Dress", "dresses", None),
    ("Little Black Dress", "dresses", None),
    ("Satin Slip Dress", "dresses", None),
    ("Striped Shirt Dress", "dresses", None),
    ("Knit Sweater Dress", "dresses", None),
    ("Tiered Maxi Dress", "dresses", None),
    ("Classic Denim Jacket", "outerwear", None),
    ("Black Leather Biker Jacket", "outerwear", None),
    ("Camel Wool Overcoat", "outerwear", None),
    ("Olive Bomber Jacket", "outerwear", None),
    ("Navy Peacoat", "outerwear", None),
    ("Quilted Puffer Vest", "outerwear", None),
]


async def seed_garments() -> None:
    await init_models()
    async with AsyncSessionFactory() as session:
        for display_name, category, source_credit in GARMENTS:
            garment_id = uuid.uuid5(uuid.NAMESPACE_DNS, display_name).hex
            image_path = f"static/garments/{garment_id}.jpg"
            statement = insert(GarmentORM).values(
                id=garment_id,
                image_path=image_path,
                category=category,
                display_name=display_name,
                source_credit=source_credit,
            )
            statement = statement.on_conflict_do_nothing(index_elements=["id"])
            await session.execute(statement)
        await session.commit()

    print(f"Seeded {len(GARMENTS)} garments.")


if __name__ == "__main__":
    asyncio.run(seed_garments())
