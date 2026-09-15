import sqlite3
from pathlib import Path

from app.core.config import settings


def get_database_path() -> Path:
    prefix = "sqlite:///"

    if not settings.database_url.startswith(prefix):
        raise ValueError(
            "Step 2 currently supports only SQLite DATABASE_URL values."
        )

    database_path = settings.database_url[len(prefix):]

    return Path(database_path)


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(get_database_path())


def init_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            INSERT OR REPLACE INTO app_meta (key, value)
            VALUES (?, ?)
            """,
            ("schema_version", "0.1"),
        )

        connection.commit()


def database_is_ready() -> bool:
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
        return True
    except sqlite3.Error:
        return False