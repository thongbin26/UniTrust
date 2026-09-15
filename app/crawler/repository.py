import json
from datetime import datetime, timezone

from app.db.database import get_connection
from app.models.notice import CrawledNotice


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def init_notice_tables() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notices (
                notice_id INTEGER PRIMARY KEY AUTOINCREMENT,

                source_id TEXT NOT NULL,
                external_id TEXT,

                canonical_url TEXT NOT NULL UNIQUE,

                title TEXT NOT NULL,
                publication_date TEXT,

                current_content_hash TEXT NOT NULL,

                first_observed_at TEXT NOT NULL,
                last_observed_at TEXT NOT NULL,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (source_id)
                    REFERENCES sources(source_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notice_versions (
                version_id INTEGER PRIMARY KEY AUTOINCREMENT,

                notice_id INTEGER NOT NULL,

                observed_at TEXT NOT NULL,
                fetched_at TEXT NOT NULL,

                content_hash TEXT NOT NULL,
                raw_html_hash TEXT NOT NULL,

                raw_text TEXT NOT NULL,
                raw_html_path TEXT NOT NULL,

                attachment_links_json TEXT NOT NULL,
                parse_mode TEXT NOT NULL,

                UNIQUE(notice_id, content_hash),

                FOREIGN KEY (notice_id)
                    REFERENCES notices(notice_id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS crawl_failures (
                failure_id INTEGER PRIMARY KEY AUTOINCREMENT,

                source_id TEXT NOT NULL,
                url TEXT,
                stage TEXT NOT NULL,

                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,

                occurred_at TEXT NOT NULL
            )
            """
        )

        connection.commit()


def save_notice(notice: CrawledNotice) -> str:
    now = utc_now().isoformat()

    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT
                notice_id,
                current_content_hash
            FROM notices
            WHERE canonical_url = ?
            """,
            (notice.canonical_url,),
        ).fetchone()

        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO notices (
                    source_id,
                    external_id,
                    canonical_url,
                    title,
                    publication_date,
                    current_content_hash,
                    first_observed_at,
                    last_observed_at,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notice.source_id,
                    notice.external_id,
                    notice.canonical_url,
                    notice.title,
                    (
                        notice.publication_date.isoformat()
                        if notice.publication_date
                        else None
                    ),
                    notice.content_hash,
                    notice.observed_at.isoformat(),
                    notice.observed_at.isoformat(),
                    now,
                    now,
                ),
            )

            notice_id = cursor.lastrowid
            status = "CREATED"

        else:
            notice_id = existing["notice_id"]

            if (
                existing["current_content_hash"]
                == notice.content_hash
            ):
                connection.execute(
                    """
                    UPDATE notices
                    SET
                        last_observed_at = ?,
                        updated_at = ?
                    WHERE notice_id = ?
                    """,
                    (
                        notice.observed_at.isoformat(),
                        now,
                        notice_id,
                    ),
                )

                connection.commit()

                return "UNCHANGED"

            connection.execute(
                """
                UPDATE notices
                SET
                    title = ?,
                    publication_date = ?,
                    current_content_hash = ?,
                    last_observed_at = ?,
                    updated_at = ?
                WHERE notice_id = ?
                """,
                (
                    notice.title,
                    (
                        notice.publication_date.isoformat()
                        if notice.publication_date
                        else None
                    ),
                    notice.content_hash,
                    notice.observed_at.isoformat(),
                    now,
                    notice_id,
                ),
            )

            status = "UPDATED"

        connection.execute(
            """
            INSERT OR IGNORE INTO notice_versions (
                notice_id,
                observed_at,
                fetched_at,
                content_hash,
                raw_html_hash,
                raw_text,
                raw_html_path,
                attachment_links_json,
                parse_mode
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                notice_id,
                notice.observed_at.isoformat(),
                notice.fetched_at.isoformat(),
                notice.content_hash,
                notice.raw_html_hash,
                notice.raw_text,
                notice.raw_html_path,
                json.dumps(
                    notice.attachment_links,
                    ensure_ascii=False,
                ),
                notice.parse_mode,
            ),
        )

        connection.commit()

        return status


def record_crawl_failure(
    source_id: str,
    url: str | None,
    stage: str,
    error: Exception,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO crawl_failures (
                source_id,
                url,
                stage,
                error_type,
                error_message,
                occurred_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                url,
                stage,
                type(error).__name__,
                str(error),
                utc_now().isoformat(),
            ),
        )

        connection.commit()


def count_notices() -> int:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM notices"
        ).fetchone()

    return int(row["total"])


def list_notices(limit: int = 20):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                n.notice_id,
                n.source_id,
                n.title,
                n.publication_date,
                n.canonical_url,
                n.current_content_hash,
                v.raw_text,
                v.parse_mode,
                v.attachment_links_json
            FROM notices AS n
            JOIN notice_versions AS v
                ON v.notice_id = n.notice_id
                AND v.content_hash = n.current_content_hash
            ORDER BY
                n.publication_date DESC,
                n.notice_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()