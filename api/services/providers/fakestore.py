from typing import List
import httpx

from .base import BaseGarmentProvider, GarmentItem

class FakeStoreProvider(BaseGarmentProvider):
    async def fetch_garments(self) -> List[GarmentItem]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://fakestoreapi.com/products")
            response.raise_for_status()
            data = response.json()

        items = []
        for item in data:
            cat_lower = item.get("category", "").lower()
            if "clothing" not in cat_lower:
                continue

            normalized_cat = "Tops"
            items.append(
                GarmentItem(
                    id=f"fakestore_{item.get('id')}",
                    title=item.get("title", ""),
                    image_url=item.get("image", ""),
                    category=normalized_cat,
                    source="FakeStore",
                )
            )
        return items
