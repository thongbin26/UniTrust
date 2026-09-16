import json

from app.extraction.draft import ExtractionDraft
from app.extraction.llm import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.extraction.providers.factory import (
    get_json_provider,
)
from app.extraction.types import ExtractionInput
from app.models.obligation import (
    CanonicalNoticeAnnotation,
)

from pathlib import Path


ANNOTATION_DIR = Path(
    "data/annotations/batch_001"
)


def load_notice(
    notice_id: int,
) -> CanonicalNoticeAnnotation:

    for path in sorted(
        ANNOTATION_DIR.glob("*.json")
    ):
        annotation = (
            CanonicalNoticeAnnotation
            .model_validate_json(
                path.read_text(
                    encoding="utf-8"
                )
            )
        )

        if (
            annotation.notice_id
            == notice_id
        ):
            return annotation

    raise RuntimeError(
        f"Notice {notice_id} not found."
    )


def main():

    notice_id = 16

    annotation = load_notice(
        notice_id
    )

    notice = (
        ExtractionInput.from_annotation(
            annotation
        )
    )

    provider = get_json_provider()

    user_prompt = build_user_prompt(
        notice,
        examples=[],
    )

    print(
        f"Provider: "
        f"{provider.provider_name}"
    )

    print(
        f"Model: "
        f"{provider.model_name}"
    )

    print(
        f"Notice: "
        f"{notice.notice_id}"
    )

    print()
    print(
        "Calling local LLM..."
    )

    raw_json = (
        provider.generate_json(
            SYSTEM_PROMPT,
            user_prompt,
            ExtractionDraft
            .model_json_schema(),
        )
    )

    print()
    print("=" * 80)
    print("RAW MODEL OUTPUT")
    print("=" * 80)
    print(raw_json)

    draft = (
        ExtractionDraft
        .model_validate_json(
            raw_json
        )
    )

    print()
    print("=" * 80)
    print("PARSED SEMANTIC DRAFT")
    print("=" * 80)

    print(
        draft.model_dump_json(
            indent=2
        )
    )

    print()
    print(
        "draft obligations =",
        len(draft.obligations),
    )

    for index, obligation in enumerate(
        draft.obligations,
        start=1,
    ):
        print()
        print(
            f"Obligation {index}:"
        )

        print(
            "action_type =",
            obligation
            .action
            .action_type,
        )

        print(
            "action_text =",
            obligation
            .action
            .text,
        )


if __name__ == "__main__":
    main()