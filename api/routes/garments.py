"""Public garment catalog routes."""

from fastapi import APIRouter, HTTPException

from api.repositories.garment_repo import (
    get_garment,
    list_garments,
)
from api.schemas import GarmentResponse

router = APIRouter(prefix="/garments", tags=["garments"])


@router.get("/", response_model=list[GarmentResponse])
async def list_garments_route(
    category: str | None = None,
) -> list[GarmentResponse]:
    """List all garments, optionally filtered by category.

    Args:
        category: Optional category filter (query parameter).

    Returns:
        A list of GarmentResponse objects.
    """
    garments = await list_garments(category)
    return [
        GarmentResponse(
            id=g.id,
            image_url=g.image_path,
            category=g.category,
            display_name=g.display_name,
            source_credit=g.source_credit,
        )
        for g in garments
    ]


@router.get("/{garment_id}", response_model=GarmentResponse)
async def get_garment_route(garment_id: str) -> GarmentResponse:
    """Get a single garment by ID.

    Args:
        garment_id: The unique garment identifier.

    Returns:
        A GarmentResponse object.

    Raises:
        HTTPException: 404 if the garment is not found.
    """
    g = await get_garment(garment_id)
    if g is None:
        raise HTTPException(status_code=404, detail="Garment not found")
    return GarmentResponse(
        id=g.id,
        image_url=g.image_path,
        category=g.category,
        display_name=g.display_name,
        source_credit=g.source_credit,
    )
