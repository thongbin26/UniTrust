import sqlite3
from pathlib import Path

from app.core.config import settings


def get_database_path() -> Path:
    prefix = "sqlite:///"

    if not settings.database_url.startswith(prefix):
        raise ValueError(
            "Current UniTrust demo supports SQLite DATABASE_URL only."
        )

    database_path = settings.database_url[len(prefix):]

    return Path(database_path)


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(get_database_path())

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


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
            ("schema_version", "0.2"),
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY,

                name TEXT NOT NULL,
                source_type TEXT NOT NULL,

                base_url TEXT NOT NULL,
                listing_url TEXT NOT NULL,

                official_domain TEXT NOT NULL,
                is_official INTEGER NOT NULL,

                expected_marker TEXT,
                provenance_note TEXT NOT NULL,

                health_status TEXT NOT NULL DEFAULT 'UNKNOWN',

                last_checked_at TEXT,
                last_success_at TEXT,

                last_http_status INTEGER,
                last_error TEXT,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS source_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,

                source_id TEXT NOT NULL,

                observed_at TEXT NOT NULL,
                fetched_at TEXT NOT NULL,

                final_url TEXT,
                http_status INTEGER,

                content_hash TEXT,
                content_length INTEGER NOT NULL DEFAULT 0,

                FOREIGN KEY (source_id)
                    REFERENCES sources(source_id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_source_snapshots_source_id
            ON source_snapshots(source_id)
            """
        )

        connection.commit()


def database_is_ready() -> bool:
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")

        return True

    except sqlite3.Error:
        return False