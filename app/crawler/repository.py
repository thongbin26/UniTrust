import json
from datetime import datetime, timezone

from app.db.database import get_connection
from app.models.notice import CrawledNotice
from app.crawler.identity import normalize_url, official_notice_id
from app.crawler.dut_parser import clean_title


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


def migrate_notice_discoveries() -> None:
    """Apply the approved Step 17C additive migration to the selected DB only."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notice_discoveries (
                discovery_id INTEGER PRIMARY KEY AUTOINCREMENT,
                notice_id INTEGER NOT NULL,
                source_id TEXT NOT NULL,
                discovery_url TEXT NOT NULL,
                normalized_discovery_url TEXT NOT NULL,
                first_discovered_at TEXT NOT NULL,
                last_discovered_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (notice_id)
                    REFERENCES notices(notice_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (source_id)
                    REFERENCES sources(source_id),
                UNIQUE (notice_id, source_id, normalized_discovery_url)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_notice_discoveries_notice_id
            ON notice_discoveries(notice_id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_notice_discoveries_source_id
            ON notice_discoveries(source_id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_notice_discoveries_normalized_url
            ON notice_discoveries(normalized_discovery_url)
            """
        )
        connection.commit()


def _has_notice_discoveries(connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'notice_discoveries'"
    ).fetchone() is not None


def _record_discovery(
    connection,
    *,
    notice_id: int,
    source_id: str,
    discovery_url: str,
    discovered_at: datetime,
    metadata: dict | None,
) -> None:
    if not _has_notice_discoveries(connection):
        return
    normalized_url = normalize_url(discovery_url)
    timestamp = discovered_at.isoformat()
    connection.execute(
        """
        INSERT INTO notice_discoveries (
            notice_id, source_id, discovery_url, normalized_discovery_url,
            first_discovered_at, last_discovered_at, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(notice_id, source_id, normalized_discovery_url)
        DO UPDATE SET
            last_discovered_at = excluded.last_discovered_at,
            metadata_json = excluded.metadata_json
        """,
        (
            notice_id,
            source_id,
            discovery_url,
            normalized_url,
            timestamp,
            timestamp,
            json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
        ),
    )


def save_notice(
    notice: CrawledNotice,
    *,
    discovery_source_id: str | None = None,
    discovery_url: str | None = None,
    discovery_metadata: dict | None = None,
) -> str:
    now = utc_now().isoformat()
    normalized_canonical_url = normalize_url(notice.canonical_url)
    shared_official_id = official_notice_id(normalized_canonical_url)
    shared_local_id = (
        shared_official_id.rsplit(":", 1)[1]
        if shared_official_id is not None
        else None
    )
    stored_external_id = notice.external_id or shared_local_id
    discovery_source_id = discovery_source_id or notice.source_id
    discovery_url = discovery_url or notice.canonical_url

    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT
                notice_id,
                current_content_hash,
                title,
                publication_date
            FROM notices
            WHERE canonical_url IN (?, ?)
            """,
            (normalized_canonical_url, notice.canonical_url),
        ).fetchone()

        resolved_by_shared_id = False
        if existing is None and shared_official_id is not None:
            candidates = connection.execute(
                """
                SELECT notice_id, current_content_hash, title,
                       publication_date, canonical_url
                FROM notices
                WHERE external_id IN (?, ?)
                ORDER BY notice_id
                """,
                (shared_local_id, shared_official_id),
            ).fetchall()
            existing = next(
                (
                    candidate
                    for candidate in candidates
                    if official_notice_id(candidate["canonical_url"])
                    == shared_official_id
                ),
                None,
            )
            resolved_by_shared_id = existing is not None

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
                    stored_external_id,
                    normalized_canonical_url,
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

            if resolved_by_shared_id:
                _record_discovery(
                    connection,
                    notice_id=notice_id,
                    source_id=discovery_source_id,
                    discovery_url=discovery_url,
                    discovered_at=notice.observed_at,
                    metadata=discovery_metadata,
                )
                connection.commit()
                return "DUPLICATE"

            current_version = connection.execute(
                """
                SELECT raw_text, attachment_links_json
                FROM notice_versions
                WHERE notice_id = ? AND content_hash = ?
                """,
                (notice_id, existing["current_content_hash"]),
            ).fetchone()
            incoming_publication_date = (
                notice.publication_date.isoformat() if notice.publication_date else None
            )
            presentation_only_title_change = (
                current_version is not None
                and existing["title"] != notice.title
                and clean_title(existing["title"]) == notice.title
                and existing["publication_date"] == incoming_publication_date
                and current_version["raw_text"] == notice.raw_text
                and json.loads(current_version["attachment_links_json"])
                == notice.attachment_links
            )

            if (
                existing["current_content_hash"]
                == notice.content_hash
                or presentation_only_title_change
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

                _record_discovery(
                    connection,
                    notice_id=notice_id,
                    source_id=discovery_source_id,
                    discovery_url=discovery_url,
                    discovered_at=notice.observed_at,
                    metadata=discovery_metadata,
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

        _record_discovery(
            connection,
            notice_id=notice_id,
            source_id=discovery_source_id,
            discovery_url=discovery_url,
            discovered_at=notice.observed_at,
            metadata=discovery_metadata,
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
