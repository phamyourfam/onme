from typing import List

from api.repositories.garment_repo import list_garments
from .base import BaseGarmentProvider, GarmentItem

class DatabaseProvider(BaseGarmentProvider):
    async def fetch_garments(self) -> List[GarmentItem]:
        # Using the existing repository pattern
        garments = await list_garments()
        return [
            GarmentItem(
                id=g.id,
                title=g.display_name,
                image_url=g.image_path,
                category=g.category.capitalize(),
                source="Database",
            )
            for g in garments
        ]
