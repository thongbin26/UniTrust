import re
from datetime import date

from app.extraction.types import ExtractionPayload


DATE_DMY_RE = re.compile(
    r"\b(?P<day>\d{1,2})"
    r"/(?P<month>\d{1,2})"
    r"/(?P<year>\d{4})\b"
)


def dates_in_raw_text(
    raw_text: str,
) -> set[str]:

    result = set()

    for match in DATE_DMY_RE.finditer(
        raw_text
    ):
        try:
            parsed = date(
                int(match.group("year")),
                int(match.group("month")),
                int(match.group("day")),
            )

            result.add(
                parsed.isoformat()
            )

        except ValueError:
            continue

    return result


def canonicalize_deadlines(
    payload: ExtractionPayload,
    raw_text: str,
) -> ExtractionPayload:

    repaired = payload.model_copy(
        deep=True
    )

    supported_dates = dates_in_raw_text(
        raw_text
    )

    for obligation in repaired.obligations:

        deadline = obligation.deadline

        if (
            deadline is None
            or not deadline.normalized
        ):
            continue

        normalized = (
            deadline.normalized[:10]
        )

        # The LLM proposed a date that cannot
        # be verified anywhere in the notice.
        if normalized not in supported_dates:
            obligation.deadline = None

    return repaired

def remove_unreferenced_evidence(
    payload: ExtractionPayload,
) -> ExtractionPayload:

    repaired = payload.model_copy(
        deep=True
    )

    referenced_ids = set()

    for obligation in repaired.obligations:

        audience = obligation.audience

        if audience:
            referenced_ids.update(
                audience.evidence_span_ids
            )

        referenced_ids.update(
            obligation.action.evidence_span_ids
        )

        if obligation.deadline:
            referenced_ids.update(
                obligation.deadline.evidence_span_ids
            )

        if obligation.amount:
            referenced_ids.update(
                obligation.amount.evidence_span_ids
            )

        if obligation.location:
            referenced_ids.update(
                obligation.location.evidence_span_ids
            )

        for document in (
            obligation.required_documents
        ):
            referenced_ids.update(
                document.evidence_span_ids
            )

        for exception in (
            obligation.exceptions
        ):
            referenced_ids.update(
                exception.evidence_span_ids
            )

    repaired.evidence_spans = [
        evidence
        for evidence
        in repaired.evidence_spans
        if evidence.evidence_id
        in referenced_ids
    ]

    return repaired