"""
SQLite database connection and schema management.

Uses Python's built-in sqlite3 module with raw SQL.
The sqlite3.Row factory is enabled so query results can be accessed
by column name (dict-like) rather than positional index.
"""

import sqlite3

from config import settings

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
    """Create the jobs table if it does not already exist.

    Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS.
    Called during FastAPI lifespan startup.
    """
    conn = get_connection()
    conn.execute(SCHEMA)
    conn.commit()
    conn.close()
