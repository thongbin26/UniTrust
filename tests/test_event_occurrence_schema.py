"""Representation-only safety tests for reviewed event/schedule facts."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.obligation import (
    ActionType, ActionValue, AnnotationStatus, CanonicalNoticeAnnotation,
    DeadlineValue, EventOccurrence, EventOccurrenceKind, EvidenceField,
    EvidenceSpan, SourceReference, StudentObligation, TemporalPrecision,
)
from app.verification.draft_lifecycle import (
    DraftLifecycleStatus, ExtractionProvenance, ObligationDraftRecord,
    ReviewerDecision,
)


def occurrence(kind=EventOccurrenceKind.EVENT, **values):
    payload = {
        "raw_text": "12/09/2026",
        "normalized_start": "2026-09-12",
        "precision": TemporalPrecision.DATE,
        "kind": kind,
        "evidence_span_ids": ["event-1"],
    }
    payload.update(values)
    return EventOccurrence(**payload)


def obligation(*, events=None, deadline=None):
    return StudentObligation(
        obligation_id="o1",
        action=ActionValue(action_type=ActionType.SUBMIT, text="nộp hồ sơ", evidence_span_ids=["action-1"]),
        deadline=deadline,
        event_occurrences=events or [],
    )


def test_event_occurrence_is_structurally_distinct_from_deadline():
    item = obligation(events=[occurrence()])
    assert item.deadline is None
    assert item.event_occurrences[0].kind is EventOccurrenceKind.EVENT


def test_supported_date_datetime_range_and_multiple_occurrences():
    date_range = occurrence(
        kind=EventOccurrenceKind.SCHEDULE,
        raw_text="01/07/2026 – 02/07/2026",
        normalized_start="2026-07-01",
        normalized_end="2026-07-02",
    )
    interview = occurrence(
        kind=EventOccurrenceKind.INTERVIEW,
        raw_text="06/10/2026 07:30",
        normalized_start="2026-10-06T07:30:00+07:00",
        precision=TemporalPrecision.DATETIME,
    )
    item = obligation(events=[date_range, interview])
    assert len(item.event_occurrences) == 2
    assert item.event_occurrences[0].normalized_end == "2026-07-02"


def test_deadline_and_interview_can_coexist_without_overwrite():
    deadline = DeadlineValue(raw_text="01/10/2026", normalized="2026-10-01", precision=TemporalPrecision.DATE)
    item = obligation(events=[occurrence(kind=EventOccurrenceKind.INTERVIEW)], deadline=deadline)
    assert item.deadline.normalized == "2026-10-01"
    assert item.event_occurrences[0].normalized_start == "2026-09-12"


def test_invalid_event_datetime_and_reversed_range_fail_closed():
    with pytest.raises(ValidationError):
        occurrence(precision=TemporalPrecision.DATETIME, normalized_start="2026-10-06T07:30:00")
    with pytest.raises(ValidationError):
        occurrence(normalized_start="2026-10-02", normalized_end="2026-10-01")


def test_old_reviewed_annotation_loads_without_event_occurrences():
    annotation = CanonicalNoticeAnnotation(
        annotation_status=AnnotationStatus.REVIEWED,
        annotator_id="reviewer",
        notice_id=1, version_id=1, source=SourceReference(source_id="dut", name="DUT"),
        title="Test", raw_text="nộp hồ sơ trước ngày 01/10/2026", observed_at=datetime.now(),
        url="https://dut.example/test", content_hash="a" * 64,
        evidence_spans=[EvidenceSpan(evidence_id="action-1", field=EvidenceField.ACTION, text="nộp hồ sơ")],
        obligations=[obligation()],
    )
    assert annotation.obligations[0].event_occurrences == []


def test_reviewed_event_occurrence_requires_referenced_source_evidence():
    with pytest.raises(ValidationError):
        CanonicalNoticeAnnotation(
            annotation_status=AnnotationStatus.REVIEWED, annotator_id="reviewer",
            notice_id=1, version_id=1, source=SourceReference(source_id="dut", name="DUT"),
            title="Test", raw_text="nộp hồ sơ 12/09/2026", observed_at=datetime.now(),
            url="https://dut.example/test", content_hash="a" * 64,
            evidence_spans=[EvidenceSpan(evidence_id="action-1", field=EvidenceField.ACTION, text="nộp hồ sơ")],
            obligations=[obligation(events=[occurrence()])],
        )


def test_draft_occurrences_stay_untrusted_until_explicit_promotion():
    record = ObligationDraftRecord(
        lifecycle_status=DraftLifecycleStatus.DRAFT, notice_id=1, version_id=1,
        source=SourceReference(source_id="dut", name="DUT"), title="Test", raw_text="nộp hồ sơ 12/09/2026",
        observed_at=datetime.now(), canonical_url="https://dut.example/test", content_hash="a" * 64,
        extraction=ExtractionProvenance(provider_id="offline-test"),
        evidence_spans=[
            EvidenceSpan(evidence_id="action-1", field=EvidenceField.ACTION, text="nộp hồ sơ"),
            EvidenceSpan(evidence_id="event-1", field=EvidenceField.EVENT_OCCURRENCE, text="12/09/2026"),
        ], obligations=[obligation(events=[occurrence()])],
    )
    assert record.as_reviewed_annotation() is None
    promoted = record.model_copy(update={
        "lifecycle_status": DraftLifecycleStatus.PROMOTED,
        "reviewer_decision": ReviewerDecision(reviewer_id="human", decided_at=datetime.now()),
    })
    assert promoted.as_reviewed_annotation().obligations[0].event_occurrences[0].kind == EventOccurrenceKind.EVENT
