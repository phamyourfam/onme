from .base import GarmentItem, BaseGarmentProvider
from .fakestore import FakeStoreProvider
from .dummyjson import DummyJsonProvider
from .database import DatabaseProvider

def get_all_providers() -> list[BaseGarmentProvider]:
    """Factory function to instantiate and return all active garment providers."""
    return [
        FakeStoreProvider(),
        DummyJsonProvider(),
        DatabaseProvider(),
    ]
