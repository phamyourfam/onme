"""Data-access layer for Moodboard persistence using raw SQLite."""

from api.database import get_connection
from api.models import Moodboard


def create_moodboard(moodboard: Moodboard) -> Moodboard:
    """Insert a new moodboard row into the database.

    Args:
        moodboard: The Moodboard dataclass instance to persist.

    Returns:
        The same Moodboard instance after successful insertion.
    """
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO moodboards (
                    id, user_id, title, canvas_state,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    moodboard.id,
                    moodboard.user_id,
                    moodboard.title,
                    moodboard.canvas_state,
                    moodboard.created_at,
                    moodboard.updated_at,
                ),
            )
    finally:
        conn.close()
    return moodboard


def get_moodboard(moodboard_id: str) -> Moodboard | None:
    """Fetch a single moodboard by its ID.

    Args:
        moodboard_id: The unique moodboard identifier.

    Returns:
        A Moodboard instance if found, None otherwise.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM moodboards WHERE id = ?",
            (moodboard_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return Moodboard(**dict(row))


def list_user_moodboards(user_id: str) -> list[Moodboard]:
    """List all moodboards owned by a specific user.

    Args:
        user_id: The unique user identifier.

    Returns:
        A list of Moodboard dataclass instances.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM moodboards WHERE user_id = ? "
            "ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    return [Moodboard(**dict(row)) for row in rows]


def update_moodboard_canvas(
    moodboard_id: str, canvas_state: str, updated_at: str
) -> None:
    """Update the canvas state and timestamp for a moodboard.

    Args:
        moodboard_id: The unique moodboard identifier.
        canvas_state: The new serialised xyflow JSON string.
        updated_at: ISO 8601 UTC timestamp of the update.
    """
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                UPDATE moodboards
                SET canvas_state = ?, updated_at = ?
                WHERE id = ?
                """,
                (canvas_state, updated_at, moodboard_id),
            )
    finally:
        conn.close()


def update_moodboard_title(
    moodboard_id: str, title: str, updated_at: str
) -> None:
    """Update the title and timestamp for a moodboard.

    Args:
        moodboard_id: The unique moodboard identifier.
        title: The new moodboard title.
        updated_at: ISO 8601 UTC timestamp of the update.
    """
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                UPDATE moodboards
                SET title = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, updated_at, moodboard_id),
            )
    finally:
        conn.close()


def delete_moodboard(moodboard_id: str, user_id: str) -> bool:
    """Delete a moodboard if it belongs to the specified user.

    Args:
        moodboard_id: The unique moodboard identifier.
        user_id: The user who must own the moodboard.

    Returns:
        True if a row was deleted, False otherwise.
    """
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "DELETE FROM moodboards WHERE id = ? AND user_id = ?",
                (moodboard_id, user_id),
            )
    finally:
        conn.close()

    return cursor.rowcount > 0
