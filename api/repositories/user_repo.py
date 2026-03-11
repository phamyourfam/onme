"""Data-access layer for User persistence using raw SQLite."""

from api.database import get_connection
from api.models import User


def create_user(user: User) -> User:
    """Insert a new user row into the database.

    Args:
        user: The User dataclass instance to persist.

    Returns:
        The same User instance after successful insertion.
    """
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO users (
                    id, email, hashed_password,
                    credits_remaining, last_credit_refresh,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.email,
                    user.hashed_password,
                    user.credits_remaining,
                    user.last_credit_refresh,
                    user.created_at,
                ),
            )
    finally:
        conn.close()
    return user


def get_user_by_email(email: str) -> User | None:
    """Fetch a single user by email address.

    Args:
        email: The email address to look up.

    Returns:
        A User instance if found, None otherwise.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return User(**dict(row))


def get_user_by_id(user_id: str) -> User | None:
    """Fetch a single user by their ID.

    Args:
        user_id: The unique user identifier.

    Returns:
        A User instance if found, None otherwise.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return User(**dict(row))


def update_user_credits(
    user_id: str, credits: int, refresh_time: str
) -> None:
    """Update credit balance and last refresh timestamp for a user.

    Args:
        user_id: The unique user identifier.
        credits: The new credit balance to set.
        refresh_time: ISO 8601 UTC timestamp of the refresh.
    """
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                UPDATE users
                SET credits_remaining = ?,
                    last_credit_refresh = ?
                WHERE id = ?
                """,
                (credits, refresh_time, user_id),
            )
    finally:
        conn.close()
