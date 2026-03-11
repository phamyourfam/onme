"""Public garment catalog routes."""

from fastapi import APIRouter, HTTPException

from api.repositories.garment_repo import (
    get_garment,
    list_garments,
)

router = APIRouter(prefix="/garments", tags=["garments"])


@router.get("/")
def list_garments_route(category: str | None = None) -> list[dict]:
    """List all garments, optionally filtered by category.

    Args:
        category: Optional category filter (query parameter).

    Returns:
        A list of garment dicts with id, image_url, category,
        display_name, and source_credit.
    """
    garments = list_garments(category)
    return [
        {
            "id": g.id,
            "image_url": g.image_path,
            "category": g.category,
            "display_name": g.display_name,
            "source_credit": g.source_credit,
        }
        for g in garments
    ]


@router.get("/{garment_id}")
def get_garment_route(garment_id: str) -> dict:
    """Get a single garment by ID.

    Args:
        garment_id: The unique garment identifier.

    Returns:
        A garment dict with id, image_url, category,
        display_name, and source_credit.

    Raises:
        HTTPException: 404 if the garment is not found.
    """
    g = get_garment(garment_id)
    if g is None:
        raise HTTPException(status_code=404, detail="Garment not found")
    return {
        "id": g.id,
        "image_url": g.image_path,
        "category": g.category,
        "display_name": g.display_name,
        "source_credit": g.source_credit,
    }
