"""Seed script to populate the garments table with sample data.

Run from the api/ directory:
    uv run python -m api.seed
"""

import uuid

from api.database import get_connection, init_db

GARMENTS = [
    # Tops
    ("Classic White T-Shirt", "tops", None),
    ("Navy Striped Polo", "tops", None),
    ("Black Crew Neck Tee", "tops", None),
    ("Linen Button-Down Shirt", "tops", None),
    ("Heather Grey Henley", "tops", None),
    ("Chambray Camp Collar Shirt", "tops", None),
    ("Ribbed Tank Top", "tops", None),
    # Bottoms
    ("Slim Fit Dark Wash Jeans", "bottoms", None),
    ("Khaki Chinos", "bottoms", None),
    ("Black Tailored Trousers", "bottoms", None),
    ("Olive Cargo Pants", "bottoms", None),
    ("Light Wash Relaxed Jeans", "bottoms", None),
    ("Navy Linen Shorts", "bottoms", None),
    ("Grey Jogger Pants", "bottoms", None),
    # Dresses
    ("Floral Midi Wrap Dress", "dresses", None),
    ("Little Black Dress", "dresses", None),
    ("Satin Slip Dress", "dresses", None),
    ("Striped Shirt Dress", "dresses", None),
    ("Knit Sweater Dress", "dresses", None),
    ("Tiered Maxi Dress", "dresses", None),
    # Outerwear
    ("Classic Denim Jacket", "outerwear", None),
    ("Black Leather Biker Jacket", "outerwear", None),
    ("Camel Wool Overcoat", "outerwear", None),
    ("Olive Bomber Jacket", "outerwear", None),
    ("Navy Peacoat", "outerwear", None),
    ("Quilted Puffer Vest", "outerwear", None),
]


def seed_garments() -> None:
    """Insert sample garments into the database.

    Uses INSERT OR IGNORE so the script is idempotent — running
    it multiple times will not create duplicate rows.
    """
    init_db()
    conn = get_connection()
    try:
        with conn:
            for display_name, category, source_credit in GARMENTS:
                garment_id = uuid.uuid5(
                    uuid.NAMESPACE_DNS, display_name
                ).hex
                image_path = f"static/garments/{garment_id}.jpg"
                conn.execute(
                    """
                    INSERT OR IGNORE INTO garments
                        (id, image_path, category,
                         display_name, source_credit)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        garment_id,
                        image_path,
                        category,
                        display_name,
                        source_credit,
                    ),
                )
    finally:
        conn.close()
    print(f"Seeded {len(GARMENTS)} garments.")


if __name__ == "__main__":
    seed_garments()
