from datetime import datetime, timezone

from app.db.database import get_connection
from app.models.source import (
    SourceCheckResult,
    SourceHealthStatus,
    SourceRead,
    SourceSeed,
)
from app.sources.seed import SEED_SOURCES


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def seed_sources() -> None:
    now = utc_now().isoformat()

    with get_connection() as connection:

        for source in SEED_SOURCES:

            connection.execute(
                """
                INSERT INTO sources (
                    source_id,
                    name,
                    source_type,
                    base_url,
                    listing_url,
                    official_domain,
                    is_official,
                    expected_marker,
                    provenance_note,
                    health_status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(source_id)
                DO UPDATE SET
                    name = excluded.name,
                    source_type = excluded.source_type,
                    base_url = excluded.base_url,
                    listing_url = excluded.listing_url,
                    official_domain = excluded.official_domain,
                    is_official = excluded.is_official,
                    expected_marker = excluded.expected_marker,
                    provenance_note = excluded.provenance_note,
                    updated_at = excluded.updated_at
                WHERE sources.name IS NOT excluded.name
                   OR sources.source_type IS NOT excluded.source_type
                   OR sources.base_url IS NOT excluded.base_url
                   OR sources.listing_url IS NOT excluded.listing_url
                   OR sources.official_domain IS NOT excluded.official_domain
                   OR sources.is_official IS NOT excluded.is_official
                   OR sources.expected_marker IS NOT excluded.expected_marker
                   OR sources.provenance_note IS NOT excluded.provenance_note
                """,
                (
                    source.source_id,
                    source.name,
                    source.source_type.value,
                    source.base_url,
                    source.listing_url,
                    source.official_domain,
                    int(source.is_official),
                    source.expected_marker,
                    source.provenance_note,
                    SourceHealthStatus.UNKNOWN.value,
                    now,
                    now,
                ),
            )

        connection.commit()


def _row_to_source(row) -> SourceRead:
    data = dict(row)

    data["is_official"] = bool(data["is_official"])

    return SourceRead.model_validate(data)


def list_sources() -> list[SourceRead]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM sources
            ORDER BY source_id
            """
        ).fetchall()

    return [_row_to_source(row) for row in rows]


def get_source(source_id: str) -> SourceRead | None:
    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT *
            FROM sources
            WHERE source_id = ?
            """,
            (source_id,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_source(row)


def save_health_result(
    result: SourceCheckResult,
) -> None:

    now = utc_now().isoformat()

    with get_connection() as connection:

        source = connection.execute(
            """
            SELECT last_success_at
            FROM sources
            WHERE source_id = ?
            """,
            (result.source_id,),
        ).fetchone()

        if source is None:
            raise ValueError(
                f"Unknown source: {result.source_id}"
            )

        last_success_at = source["last_success_at"]

        if result.health_status == SourceHealthStatus.HEALTHY:
            last_success_at = result.checked_at.isoformat()

        connection.execute(
            """
            UPDATE sources
            SET
                health_status = ?,
                last_checked_at = ?,
                last_success_at = ?,
                last_http_status = ?,
                last_error = ?,
                updated_at = ?
            WHERE source_id = ?
            """,
            (
                result.health_status.value,
                result.checked_at.isoformat(),
                last_success_at,
                result.http_status,
                result.error,
                now,
                result.source_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO source_snapshots (
                source_id,
                observed_at,
                fetched_at,
                final_url,
                http_status,
                content_hash,
                content_length
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.source_id,
                result.checked_at.isoformat(),
                result.checked_at.isoformat(),
                result.final_url,
                result.http_status,
                result.content_hash,
                result.content_length,
            ),
        )

        connection.commit()
