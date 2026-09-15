import json
from datetime import datetime, timezone

from app.db.database import get_connection
from app.models.obligation import (
    CanonicalNoticeAnnotation,
)


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def init_annotation_tables() -> None:
    with get_connection() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS
            annotation_documents (
                annotation_id INTEGER
                    PRIMARY KEY AUTOINCREMENT,

                notice_id INTEGER NOT NULL,
                version_id INTEGER NOT NULL,

                schema_version TEXT NOT NULL,

                annotator_id TEXT NOT NULL,
                annotation_status TEXT NOT NULL,

                annotation_json TEXT NOT NULL,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                UNIQUE (
                    notice_id,
                    version_id,
                    schema_version,
                    annotator_id
                ),

                FOREIGN KEY (notice_id)
                    REFERENCES notices(notice_id),

                FOREIGN KEY (version_id)
                    REFERENCES notice_versions(version_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS
            temporal_relations (
                relation_id INTEGER
                    PRIMARY KEY AUTOINCREMENT,

                source_notice_id INTEGER NOT NULL,
                source_version_id INTEGER NOT NULL,

                target_notice_id INTEGER NOT NULL,
                target_version_id INTEGER,

                relation_type TEXT NOT NULL,

                changed_fields_json TEXT
                    NOT NULL DEFAULT '[]',

                evidence_span_ids_json TEXT
                    NOT NULL DEFAULT '[]',

                note TEXT,

                provenance TEXT NOT NULL
                    DEFAULT 'manual',

                created_at TEXT NOT NULL,

                FOREIGN KEY (source_notice_id)
                    REFERENCES notices(notice_id),

                FOREIGN KEY (target_notice_id)
                    REFERENCES notices(notice_id)
            )
            """
        )

        connection.commit()


def save_annotation(
    annotation: CanonicalNoticeAnnotation,
) -> None:

    now = utc_now().isoformat()

    payload = annotation.model_dump_json()

    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO annotation_documents (
                notice_id,
                version_id,
                schema_version,
                annotator_id,
                annotation_status,
                annotation_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT (
                notice_id,
                version_id,
                schema_version,
                annotator_id
            )
            DO UPDATE SET
                annotation_status =
                    excluded.annotation_status,

                annotation_json =
                    excluded.annotation_json,

                updated_at =
                    excluded.updated_at
            """,
            (
                annotation.notice_id,
                annotation.version_id,
                annotation.schema_version,
                annotation.annotator_id,
                annotation.annotation_status.value,
                payload,
                now,
                now,
            ),
        )

        connection.commit()