from abc import ABC, abstractmethod
from typing import List

from pydantic import BaseModel

class GarmentItem(BaseModel):
    id: str
    title: str
    image_url: str
    category: str
    source: str

class BaseGarmentProvider(ABC):
    @abstractmethod
    async def fetch_garments(self) -> List[GarmentItem]:
        """Fetch a list of normalized GarmentItem objects."""
        pass
