"""
SQLite database connection and schema management.

Uses Python's built-in sqlite3 module with raw SQL.
The sqlite3.Row factory is enabled so query results can be accessed
by column name (dict-like) rather than positional index.
"""

import sqlite3

from api.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id                   TEXT PRIMARY KEY,
    status               TEXT NOT NULL DEFAULT 'pending',
    model_name           TEXT NOT NULL,
    person_image_path    TEXT NOT NULL,
    garment_image_path   TEXT NOT NULL,
    result_image_path    TEXT,
    intermediate_outputs TEXT,
    error_message        TEXT,
    current_stage        TEXT,
    created_at           TEXT NOT NULL,
    completed_at         TEXT,
    preprocessing_ms     INTEGER,
    inference_ms         INTEGER,
    postprocessing_ms    INTEGER
);

CREATE TABLE IF NOT EXISTS users (
    id                   TEXT PRIMARY KEY,
    email                TEXT UNIQUE NOT NULL,
    hashed_password      TEXT NOT NULL,
    credits_remaining    INTEGER NOT NULL DEFAULT 10,
    last_credit_refresh  TEXT NOT NULL,
    created_at           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS garments (
    id                   TEXT PRIMARY KEY,
    image_path           TEXT NOT NULL,
    category             TEXT NOT NULL,
    display_name         TEXT NOT NULL,
    source_credit        TEXT
);

CREATE TABLE IF NOT EXISTS moodboards (
    id                   TEXT PRIMARY KEY,
    user_id              TEXT NOT NULL,
    title                TEXT NOT NULL DEFAULT 'Untitled',
    canvas_state         TEXT,
    created_at           TEXT NOT NULL,
    updated_at           TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    """Open a connection to the SQLite database.

    Returns a connection with Row factory enabled, allowing
    column access by name via dict(row).

    Returns:
        An open sqlite3.Connection instance. Caller is
        responsible for closing it.
    """
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they do not already exist.

    Also adds a user_id column to the jobs table for existing
    databases. The ALTER TABLE is wrapped in try/except for
    idempotency — it silently passes if the column already exists.

    Safe to call multiple times. Called during FastAPI lifespan startup.
    """
    conn = get_connection()
    conn.executescript(SCHEMA)
    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN user_id TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.close()
