import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from app.models.obligation import (
    AnnotationStatus,
    CanonicalNoticeAnnotation,
)


def load_json_files(
    path: Path,
) -> list[tuple[Path, dict]]:

    items = []

    if path.is_dir():
        for file_path in sorted(
            path.glob("*.json")
        ):
            data = json.loads(
                file_path.read_text(
                    encoding="utf-8"
                )
            )

            items.append(
                (file_path, data)
            )

        return items

    if path.suffix == ".jsonl":
        lines = path.read_text(
            encoding="utf-8"
        ).splitlines()

        for index, line in enumerate(
            lines,
            start=1,
        ):
            if not line.strip():
                continue

            items.append(
                (
                    Path(
                        f"{path}:line-{index}"
                    ),
                    json.loads(line),
                )
            )

        return items

    raise ValueError(
        "Expected a directory of JSON files "
        "or a .jsonl file."
    )


def validate_semantics(
    annotation:
        CanonicalNoticeAnnotation,
    require_complete: bool,
) -> list[str]:

    errors = []

    if require_complete:
        if annotation.annotation_status not in {
            AnnotationStatus.REVIEWED,
            AnnotationStatus.GOLD,
        }:
            errors.append(
                "annotation_status must be REVIEWED or GOLD"
            )

        if annotation.annotator_id in {
            "UNASSIGNED",
            "AI_DRAFT",
        }:
            errors.append(
                "annotation must be confirmed by a human annotator"
            )

    evidence_texts = {
        evidence.text
        for evidence
        in annotation.evidence_spans
    }

    for evidence_text in evidence_texts:
        if (
            evidence_text
            not in annotation.raw_text
        ):
            errors.append(
                "Evidence quote does not occur "
                f"in raw_text: {evidence_text!r}"
            )

    return errors


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "path",
    )

    parser.add_argument(
        "--require-complete",
        action="store_true",
    )

    args = parser.parse_args()

    path = Path(args.path)

    records = load_json_files(
        path
    )

    valid = 0
    invalid = 0

    for file_path, data in records:
        try:
            annotation = (
                CanonicalNoticeAnnotation
                .model_validate(data)
            )

            errors = (
                validate_semantics(
                    annotation,
                    args.require_complete,
                )
            )

            if errors:
                invalid += 1

                print(
                    f"FAIL {file_path}"
                )

                for error in errors:
                    print(
                        f"  - {error}"
                    )

                continue

            valid += 1

            print(
                f"PASS {file_path}"
            )

        except (
            ValidationError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:

            invalid += 1

            print(
                f"FAIL {file_path}"
            )

            print(
                f"  {exc}"
            )

    print()
    print("=" * 70)

    print(
        f"valid   = {valid}"
    )

    print(
        f"invalid = {invalid}"
    )

    if invalid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()