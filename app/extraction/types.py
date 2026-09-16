from datetime import datetime

from pydantic import BaseModel, Field

from app.models.obligation import (
    CanonicalNoticeAnnotation,
    EvidenceSpan,
    SourceReference,
    StudentObligation,
)


class ExtractionInput(BaseModel):
    notice_id: int
    version_id: int

    source: SourceReference

    title: str
    raw_text: str

    publication_time: datetime | None = None
    observed_at: datetime

    url: str
    content_hash: str

    @classmethod
    def from_annotation(
        cls,
        annotation: CanonicalNoticeAnnotation,
    ):
        return cls(
            notice_id=annotation.notice_id,
            version_id=annotation.version_id,
            source=annotation.source,
            title=annotation.title,
            raw_text=annotation.raw_text,
            publication_time=annotation.publication_time,
            observed_at=annotation.observed_at,
            url=annotation.url,
            content_hash=annotation.content_hash,
        )


class ExtractionPayload(BaseModel):
    evidence_spans: list[EvidenceSpan] = Field(
        default_factory=list
    )

    obligations: list[StudentObligation] = Field(
        default_factory=list
    )


class ExtractionRun(BaseModel):
    method: str

    notice_id: int

    provider: str | None = None
    model: str | None = None

    latency_ms: float

    error: str | None = None

    prediction: (
        CanonicalNoticeAnnotation | None
    ) = None