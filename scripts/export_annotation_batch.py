import json
from pathlib import Path

from app.annotations.repository import (
    init_annotation_tables,
)
from app.db.database import get_connection
from app.models.obligation import (
    AnnotationStatus,
    CanonicalNoticeAnnotation,
    SourceReference,
)


OUTPUT_DIR = Path(
    "data/annotations/batch_001"
)


KEYWORDS = (
    "sinh viên",
    "đăng ký",
    "nộp",
    "học phí",
    "lệ phí",
    "thời hạn",
    "hạn",
    "tham gia",
    "địa điểm",
    "hồ sơ",
    "thời gian",
    "thu",
)


SOURCE_QUOTAS = {
    "dut_academic": 4,
    "dut_ctsv": 3,
    "dut_it_faculty": 3,
}


def obligation_score(
    title: str,
    raw_text: str,
) -> int:

    text = (
        title
        + "\n"
        + raw_text
    ).casefold()

    return sum(
        1
        for keyword in KEYWORDS
        if keyword in text
    )


def load_candidates():
    with get_connection() as connection:
        return connection.execute(
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
                v.raw_text,
                v.parse_mode

            FROM notices AS n

            JOIN sources AS s
                ON s.source_id = n.source_id

            JOIN notice_versions AS v
                ON v.notice_id = n.notice_id
                AND v.content_hash =
                    n.current_content_hash

            WHERE
                v.parse_mode = 'body'
                AND LENGTH(v.raw_text) >= 80
            """
        ).fetchall()


def select_batch(
    candidates,
):
    scored = []

    for row in candidates:
        scored.append(
            (
                obligation_score(
                    row["title"],
                    row["raw_text"],
                ),
                row,
            )
        )

    scored.sort(
        key=lambda item: (
            -item[0],
            -item[1]["notice_id"],
        )
    )

    selected = []
    selected_ids = set()

    for source_id, quota in (
        SOURCE_QUOTAS.items()
    ):
        source_rows = [
            item
            for item in scored
            if item[1]["source_id"]
            == source_id
        ]

        for score, row in (
            source_rows[:quota]
        ):
            selected.append(
                (score, row)
            )

            selected_ids.add(
                row["notice_id"]
            )

    # Fallback if one source does not
    # contain enough body notices.
    for score, row in scored:
        if len(selected) >= 10:
            break

        if (
            row["notice_id"]
            in selected_ids
        ):
            continue

        selected.append(
            (score, row)
        )

        selected_ids.add(
            row["notice_id"]
        )

    return selected[:10]


def main():
    init_annotation_tables()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    selected = select_batch(
        load_candidates()
    )

    if len(selected) < 10:
        raise RuntimeError(
            "Fewer than 10 suitable body "
            "notices are available."
        )

    print()
    print(
        "UniTrust Annotation Batch 001"
    )
    print("=" * 90)

    for index, (score, row) in enumerate(
        selected,
        start=1,
    ):
        annotation = (
            CanonicalNoticeAnnotation(
                annotation_status=(
                    AnnotationStatus.TODO
                ),
                annotator_id="UNASSIGNED",

                notice_id=row[
                    "notice_id"
                ],

                version_id=row[
                    "version_id"
                ],

                source=SourceReference(
                    source_id=row[
                        "source_id"
                    ],
                    name=row[
                        "source_name"
                    ],
                ),

                title=row["title"],

                raw_text=row[
                    "raw_text"
                ],

                publication_time=row[
                    "publication_date"
                ],

                observed_at=row[
                    "observed_at"
                ],

                url=row[
                    "canonical_url"
                ],

                content_hash=row[
                    "current_content_hash"
                ],

                evidence_spans=[],
                obligations=[],
                temporal_relations=[],
            )
        )

        path = (
            OUTPUT_DIR
            / (
                f"{index:02d}_"
                f"notice_"
                f"{row['notice_id']}.json"
            )
        )

        path.write_text(
            annotation.model_dump_json(
                indent=2
            ),
            encoding="utf-8",
        )

        print(
            f"{index:02d}. "
            f"notice_id="
            f"{row['notice_id']:<3} "
            f"source="
            f"{row['source_id']:<15} "
            f"score={score}"
        )

        print(
            f"    {row['title']}"
        )

    print("=" * 90)

    print(
        f"Templates written to: "
        f"{OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()