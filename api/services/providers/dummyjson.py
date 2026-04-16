import asyncio
from typing import List
import httpx

from .base import BaseGarmentProvider, GarmentItem

class DummyJsonProvider(BaseGarmentProvider):
    async def fetch_garments(self) -> List[GarmentItem]:
        categories = ["mens-shirts", "womens-dresses", "tops"]
        
        async def fetch_cat(client: httpx.AsyncClient, cat: str):
            try:
                resp = await client.get(f"https://dummyjson.com/products/category/{cat}")
                resp.raise_for_status()
                return resp.json().get("products", [])
            except Exception:
                return []

        async with httpx.AsyncClient(timeout=10.0) as client:
            results = await asyncio.gather(*[fetch_cat(client, c) for c in categories])
            
        items = []
        for product_list in results:
            for item in product_list:
                cat = item.get("category", "")
                if "dress" in cat:
                    normalized = "Dresses"
                else:
                    normalized = "Tops"
                    
                items.append(
                    GarmentItem(
                        id=f"dummyjson_{item.get('id')}",
                        title=item.get("title", ""),
                        image_url=item.get("thumbnail", ""),
                        category=normalized,
                        source="DummyJSON",
                    )
                )
        return items
