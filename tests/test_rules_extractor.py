from datetime import (
    datetime,
    timezone,
)

from app.extraction.rules import (
    RuleExtractor,
)
from app.extraction.types import (
    ExtractionInput,
)
from app.models.obligation import (
    SourceReference,
)


def test_rules_extract_date_money():

    raw_text = (
        "Sinh viên khóa 2026 "
        "nộp lệ phí 450.000 đồng "
        "trước ngày 20/09/2026 "
        "tại Phòng A101."
    )

    notice = ExtractionInput(
        notice_id=999,
        version_id=999,

        source=SourceReference(
            source_id="fixture",
            name="Fixture",
        ),

        title="Fixture",

        raw_text=raw_text,

        publication_time=None,

        observed_at=datetime.now(
            timezone.utc
        ),

        url=(
            "https://example.invalid"
        ),

        content_hash="abc",
    )

    run = RuleExtractor().extract(
        notice
    )

    assert run.error is None
    assert run.prediction is not None

    assert all(
        evidence.text
        in raw_text
        for evidence
        in run.prediction
        .evidence_spans
    )

    amounts = {
        obligation.amount.value_vnd
        for obligation
        in run.prediction.obligations
        if obligation.amount
    }

    assert 450000 in amounts

    deadlines = {
        obligation.deadline.normalized
        for obligation
        in run.prediction.obligations
        if obligation.deadline
    }

    assert (
        "2026-09-20"
        in deadlines
    )