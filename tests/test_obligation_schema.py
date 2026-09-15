from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.obligation import (
    ActionType,
    ActionValue,
    AnnotationStatus,
    CanonicalNoticeAnnotation,
    DeadlineValue,
    EvidenceField,
    EvidenceSpan,
    SourceReference,
    StudentObligation,
    TemporalPrecision,
)


def make_annotation():
    raw_text = (
        "Sinh viên khóa 2026 đăng ký "
        "trước ngày 20/09/2026."
    )

    return CanonicalNoticeAnnotation(
        annotation_status=(
            AnnotationStatus.REVIEWED
        ),

        annotator_id="tester",

        notice_id=1,
        version_id=1,

        source=SourceReference(
            source_id="dut_academic",
            name="DUT Academic",
        ),

        title="Test notice",

        raw_text=raw_text,

        observed_at=datetime.now(
            timezone.utc
        ),

        url=(
            "https://dut.udn.vn/"
            "test"
        ),

        content_hash="abc",

        evidence_spans=[
            EvidenceSpan(
                evidence_id="e1",
                field=EvidenceField.ACTION,
                text="đăng ký",
            )
        ],

        obligations=[
            StudentObligation(
                obligation_id="o1",

                action=ActionValue(
                    action_type=(
                        ActionType.REGISTER
                    ),

                    text="đăng ký",

                    evidence_span_ids=[
                        "e1"
                    ],
                ),

                deadline=DeadlineValue(
                    raw_text=(
                        "20/09/2026"
                    ),

                    normalized=(
                        "2026-09-20"
                    ),

                    precision=(
                        TemporalPrecision.DATE
                    ),
                ),
            )
        ],
    )


def test_valid_annotation():
    annotation = make_annotation()

    assert (
        annotation.schema_version
        == "0.1"
    )

    assert (
        len(annotation.obligations)
        == 1
    )


def test_unknown_evidence_reference_fails():
    annotation = make_annotation()

    data = annotation.model_dump()

    data["obligations"][0][
        "action"
    ][
        "evidence_span_ids"
    ] = ["missing"]

    with pytest.raises(
        ValidationError
    ):
        CanonicalNoticeAnnotation(
            **data
        )


def test_invalid_date_fails():
    annotation = make_annotation()

    data = annotation.model_dump()

    data["obligations"][0][
        "deadline"
    ][
        "normalized"
    ] = "20-09-2026"

    with pytest.raises(
        ValidationError
    ):
        CanonicalNoticeAnnotation(
            **data
        )