import json
import re
from pathlib import Path

from app.db.database import get_connection
from app.models.obligation import CanonicalNoticeAnnotation


BATCH_DIR = Path("data/annotations/batch_001")

NOTICE_ID_RE = re.compile(r"notice_(\d+)\.json$")


def get_notice_metadata(notice_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                n.notice_id,
                n.source_id,
                s.name AS source_name,
                n.title,
                n.publication_date,
                n.canonical_url,
                n.current_content_hash,

                v.version_id,
                v.observed_at,
                v.raw_text

            FROM notices AS n

            JOIN sources AS s
                ON s.source_id = n.source_id

            JOIN notice_versions AS v
                ON v.notice_id = n.notice_id
                AND v.content_hash = n.current_content_hash

            WHERE n.notice_id = ?
            """,
            (notice_id,),
        ).fetchone()

    if row is None:
        raise ValueError(
            f"Notice {notice_id} not found in database."
        )

    return {
        "schema_version": "0.1",

        "notice_id": row["notice_id"],
        "version_id": row["version_id"],

        "source": {
            "source_id": row["source_id"],
            "name": row["source_name"],
        },

        "title": row["title"],
        "raw_text": row["raw_text"],

        "publication_time": row["publication_date"],
        "observed_at": row["observed_at"],

        "url": row["canonical_url"],
        "content_hash": row["current_content_hash"],
    }


def main() -> None:
    files = sorted(
        BATCH_DIR.glob("*.json")
    )

    if not files:
        raise RuntimeError(
            "No annotation JSON files found."
        )

    repaired = 0

    for path in files:
        match = NOTICE_ID_RE.search(path.name)

        if not match:
            print(f"SKIP {path.name}")
            continue

        notice_id = int(match.group(1))

        # Current file contains the annotation work.
        current = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        metadata = get_notice_metadata(
            notice_id
        )

        # Preserve human/AI annotation fields.
        repaired_data = {
            **metadata,

            "annotation_status": current.get(
                "annotation_status",
                "DRAFT",
            ),

            "annotator_id": current.get(
                "annotator_id",
                "AI_DRAFT",
            ),

            "evidence_spans": current.get(
                "evidence_spans",
                [],
            ),

            "obligations": current.get(
                "obligations",
                [],
            ),

            "temporal_relations": current.get(
                "temporal_relations",
                [],
            ),

            "notes": current.get(
                "notes"
            ),
        }

        # Validate before overwriting the file.
        validated = (
            CanonicalNoticeAnnotation
            .model_validate(
                repaired_data
            )
        )

        path.write_text(
            validated.model_dump_json(
                indent=2
            ),
            encoding="utf-8",
        )

        repaired += 1

        print(
            f"REPAIRED {path.name} "
            f"(notice_id={notice_id}, "
            f"version_id={validated.version_id})"
        )

    print()
    print(
        f"Repaired files: {repaired}"
    )


if __name__ == "__main__":
    main()