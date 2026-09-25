"""Provider-neutral, version-bound lifecycle records for future extraction.

These records deliberately do not make an extracted obligation trustworthy.
Only an explicit human promotion can be adapted into the existing reviewed
annotation boundary used by verification.
"""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.models.obligation import (
    AnnotationStatus,
    CanonicalNoticeAnnotation,
    EvidenceSpan,
    SourceReference,
    StudentObligation,
    TemporalRelation,
)


class DraftLifecycleStatus(StrEnum):
    DRAFT = "DRAFT"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"


class ExtractionProvenance(BaseModel):
    """Non-secret metadata describing how a draft was produced."""

    provider_id: str = Field(min_length=1)
    model_id: str | None = None
    extracted_at: datetime | None = None


class ReviewerDecision(BaseModel):
    reviewer_id: str = Field(min_length=1)
    decided_at: datetime
    note: str | None = None


class ObligationDraftRecord(BaseModel):
    """A future extraction result bound to one immutable notice version.

    The record intentionally carries the same evidence-backed obligation shape
    as a canonical annotation.  Promotion is therefore an explicit adapter,
    not a second verifier data model.
    """

    schema_version: str = "0.1"
    lifecycle_status: DraftLifecycleStatus

    notice_id: int
    version_id: int
    source: SourceReference
    title: str
    raw_text: str
    observed_at: datetime
    canonical_url: str
    content_hash: str

    extraction: ExtractionProvenance
    reviewer_decision: ReviewerDecision | None = None

    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    obligations: list[StudentObligation] = Field(default_factory=list)
    temporal_relations: list[TemporalRelation] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_human_decision_for_terminal_states(self):
        if self.lifecycle_status in {
            DraftLifecycleStatus.PROMOTED,
            DraftLifecycleStatus.REJECTED,
        } and self.reviewer_decision is None:
            raise ValueError("Promoted or rejected drafts require reviewer decision metadata.")
        return self

    def as_reviewed_annotation(self) -> CanonicalNoticeAnnotation | None:
        """Return trusted evidence only for an explicitly promoted record."""
        if self.lifecycle_status is not DraftLifecycleStatus.PROMOTED:
            return None
        assert self.reviewer_decision is not None
        return CanonicalNoticeAnnotation(
            schema_version=self.schema_version,
            annotation_status=AnnotationStatus.REVIEWED,
            annotator_id=self.reviewer_decision.reviewer_id,
            notice_id=self.notice_id,
            version_id=self.version_id,
            source=self.source,
            title=self.title,
            raw_text=self.raw_text,
            observed_at=self.observed_at,
            url=self.canonical_url,
            content_hash=self.content_hash,
            evidence_spans=self.evidence_spans,
            obligations=self.obligations,
            temporal_relations=self.temporal_relations,
            notes=self.reviewer_decision.note,
        )
