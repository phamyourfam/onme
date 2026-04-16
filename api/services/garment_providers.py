import asyncio
import json
from abc import ABC, abstractmethod
from typing import List

import httpx
from pydantic import BaseModel

from api.repositories.garment_repo import list_garments


class GarmentItem(BaseModel):
    id: str
    title: str
    image_url: str
    category: str
    source: str


class BaseGarmentProvider(ABC):
    @abstractmethod
    async def fetch_garments(self) -> List[GarmentItem]:
        pass


class FakeStoreProvider(BaseGarmentProvider):
    async def fetch_garments(self) -> List[GarmentItem]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://fakestoreapi.com/products")
            response.raise_for_status()
            data = response.json()

        items = []
        for item in data:
            category_raw = item.get("category", "")
            cat_lower = category_raw.lower()
            
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


class PlatziStoreProvider(BaseGarmentProvider):
    async def fetch_garments(self) -> List[GarmentItem]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # categoryId=1 is clothes
            response = await client.get("https://api.escuelajs.co/api/v1/products/?categoryId=1")
            response.raise_for_status()
            data = response.json()

        items = []
        for item in data:
            images = item.get("images", [])
            image_url = images[0] if images else ""
            if image_url and image_url.startswith('["'):
                try:
                    img_list = json.loads(image_url)
                    image_url = img_list[0] if img_list else image_url
                except Exception:
                    pass

            url_lower = image_url.lower()
            if any(bad in url_lower for bad in ["placeimg", "placeholder", "imgur.com", "any"]):
                continue

            items.append(
                GarmentItem(
                    id=f"platzi_{item.get('id')}",
                    title=item.get("title", ""),
                    image_url=image_url,
                    category="Outerwear",  # Platzi clothing category
                    source="PlatziStore",
                )
            )
        return items


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
