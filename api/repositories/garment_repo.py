"""Data-access layer for Garment persistence using raw SQLite."""

from api.database import get_connection
from api.models import Garment


def list_garments(category: str | None = None) -> list[Garment]:
    """List all garments, optionally filtered by category.

    Args:
        category: If provided, only return garments in this category.

    Returns:
        A list of Garment dataclass instances.
    """
    conn = get_connection()
    try:
        if category:
            rows = conn.execute(
                "SELECT * FROM garments WHERE category = ?",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM garments").fetchall()
    finally:
        conn.close()

    return [Garment(**dict(row)) for row in rows]


def get_garment(garment_id: str) -> Garment | None:
    """Fetch a single garment by its ID.

    Args:
        garment_id: The unique garment identifier.

    Returns:
        A Garment instance if found, None otherwise.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM garments WHERE id = ?",
            (garment_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return Garment(**dict(row))
