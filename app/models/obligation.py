from datetime import datetime, date
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


SCHEMA_VERSION = "0.1"


class AnnotationStatus(StrEnum):
    TODO = "TODO"
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    GOLD = "GOLD"
    EXAMPLE = "EXAMPLE"


class EvidenceField(StrEnum):
    AUDIENCE = "audience"
    ACTION = "action"
    DEADLINE = "deadline"
    EVENT_OCCURRENCE = "event_occurrence"
    AMOUNT = "amount"
    LOCATION = "location"
    REQUIRED_DOCUMENT = "required_document"
    EXCEPTION = "exception"
    TEMPORAL_RELATION = "temporal_relation"


class ActionType(StrEnum):
    REGISTER = "register"
    APPLY = "apply"
    PAY = "pay"
    SUBMIT = "submit"
    ATTEND = "attend"
    COLLECT = "collect"
    UPDATE = "update"
    CHECK = "check"
    OTHER = "other"


class TemporalPrecision(StrEnum):
    DATE = "date"
    DATETIME = "datetime"
    UNKNOWN = "unknown"


class EventOccurrenceKind(StrEnum):
    """Role of an obligation-related occurrence, never a completion deadline."""

    EVENT = "event"
    SCHEDULE = "schedule"
    INTERVIEW = "interview"
    AWARD = "award"


class TemporalRelationType(StrEnum):
    AMENDS = "amends"
    SUPERSEDES = "supersedes"
    DUPLICATES = "duplicates"
    RELATED = "related"


class MaterialField(StrEnum):
    AUDIENCE = "audience"
    ACTION = "action"
    DEADLINE = "deadline"
    AMOUNT = "amount"
    LOCATION = "location"
    REQUIRED_DOCUMENTS = "required_documents"
    EXCEPTIONS = "exceptions"


class SourceReference(BaseModel):
    source_id: str
    name: str


class EvidenceSpan(BaseModel):
    evidence_id: str

    field: EvidenceField

    # Exact quote copied from raw_text.
    text: str = Field(min_length=1)

    # Optional in schema v0.1.
    # When present, offsets refer to raw_text.
    start_char: int | None = Field(
        default=None,
        ge=0,
    )

    end_char: int | None = Field(
        default=None,
        ge=1,
    )

    @model_validator(mode="after")
    def validate_offsets(self):
        if (
            self.start_char is None
            and self.end_char is None
        ):
            return self

        if (
            self.start_char is None
            or self.end_char is None
        ):
            raise ValueError(
                "start_char and end_char must either "
                "both be set or both be null."
            )

        if self.end_char <= self.start_char:
            raise ValueError(
                "end_char must be greater than start_char."
            )

        return self


class EvidenceBackedText(BaseModel):
    text: str = Field(min_length=1)

    evidence_span_ids: list[str] = Field(
        default_factory=list
    )


class AudienceCondition(BaseModel):
    raw_text: str | None = None

    applies_to_all_students: bool = False

    faculties: list[str] = Field(
        default_factory=list
    )

    majors: list[str] = Field(
        default_factory=list
    )

    cohorts: list[str] = Field(
        default_factory=list
    )

    programs: list[str] = Field(
        default_factory=list
    )

    evidence_span_ids: list[str] = Field(
        default_factory=list
    )


class ActionValue(BaseModel):
    action_type: ActionType

    text: str = Field(min_length=1)

    evidence_span_ids: list[str] = Field(
        default_factory=list
    )


class DeadlineValue(BaseModel):
    raw_text: str = Field(min_length=1)

    # ISO 8601:
    # 2026-09-20
    # OR
    # 2026-09-20T17:00:00+07:00
    normalized: str | None = None

    precision: TemporalPrecision

    timezone: str = "Asia/Ho_Chi_Minh"

    evidence_span_ids: list[str] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validate_normalized_value(self):
        if self.normalized is None:
            return self

        if self.precision == TemporalPrecision.DATE:
            date.fromisoformat(
                self.normalized
            )

        elif (
            self.precision
            == TemporalPrecision.DATETIME
        ):
            parsed = datetime.fromisoformat(
                self.normalized
            )

            if parsed.tzinfo is None:
                raise ValueError(
                    "Normalized datetime must "
                    "include timezone."
                )

        return self


class EventOccurrence(BaseModel):
    """Reviewed event or schedule metadata associated with an obligation.

    This is structurally separate from ``DeadlineValue`` so an event date can
    never silently be compared as a completion deadline.
    """

    raw_text: str = Field(min_length=1)
    normalized_start: str | None = None
    normalized_end: str | None = None
    precision: TemporalPrecision
    kind: EventOccurrenceKind
    location: EvidenceBackedText | None = None
    audience: AudienceCondition | None = None
    evidence_span_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_normalized_values(self):
        for value in (self.normalized_start, self.normalized_end):
            if value is None:
                continue
            if self.precision == TemporalPrecision.DATE:
                date.fromisoformat(value)
            elif self.precision == TemporalPrecision.DATETIME:
                parsed = datetime.fromisoformat(value)
                if parsed.tzinfo is None:
                    raise ValueError("Normalized event datetime must include timezone.")
        if self.normalized_start and self.normalized_end and self.normalized_end < self.normalized_start:
            raise ValueError("Event occurrence end cannot precede its start.")
        return self


class MoneyValue(BaseModel):
    raw_text: str = Field(min_length=1)

    # Integer Vietnamese dong.
    value_vnd: int = Field(ge=0)

    currency: str = "VND"

    evidence_span_ids: list[str] = Field(
        default_factory=list
    )


class StudentObligation(BaseModel):
    obligation_id: str

    audience: AudienceCondition | None = None

    action: ActionValue

    deadline: DeadlineValue | None = None

    # Representation only: current verification does not compare this field.
    event_occurrences: list[EventOccurrence] = Field(default_factory=list)

    amount: MoneyValue | None = None

    location: EvidenceBackedText | None = None

    required_documents: list[
        EvidenceBackedText
    ] = Field(
        default_factory=list
    )

    exceptions: list[
        EvidenceBackedText
    ] = Field(
        default_factory=list
    )


class TemporalRelation(BaseModel):
    relation_type: TemporalRelationType

    target_notice_id: int

    target_version_id: int | None = None

    changed_fields: list[
        MaterialField
    ] = Field(
        default_factory=list
    )

    evidence_span_ids: list[str] = Field(
        default_factory=list
    )

    note: str | None = None


class CanonicalNoticeAnnotation(BaseModel):
    schema_version: str = SCHEMA_VERSION

    annotation_status: AnnotationStatus

    annotator_id: str

    notice_id: int
    version_id: int

    source: SourceReference

    title: str

    raw_text: str

    publication_time: datetime | None = None

    observed_at: datetime

    url: str

    content_hash: str

    evidence_spans: list[
        EvidenceSpan
    ] = Field(
        default_factory=list
    )

    obligations: list[
        StudentObligation
    ] = Field(
        default_factory=list
    )

    temporal_relations: list[
        TemporalRelation
    ] = Field(
        default_factory=list
    )

    notes: str | None = None

    @model_validator(mode="after")
    def validate_evidence_references(self):
        evidence_ids = [
            evidence.evidence_id
            for evidence in self.evidence_spans
        ]

        if len(evidence_ids) != len(
            set(evidence_ids)
        ):
            raise ValueError(
                "evidence_id values must be unique."
            )

        evidence_set = set(
            evidence_ids
        )

        def check_ids(
            ids: list[str],
            context: str,
        ):
            missing = (
                set(ids)
                - evidence_set
            )

            if missing:
                raise ValueError(
                    f"{context} references "
                    f"unknown evidence IDs: "
                    f"{sorted(missing)}"
                )

        for evidence in self.evidence_spans:
            if (
                evidence.start_char is not None
                and evidence.end_char is not None
            ):
                actual = self.raw_text[
                    evidence.start_char:
                    evidence.end_char
                ]

                if actual != evidence.text:
                    raise ValueError(
                        f"Evidence {evidence.evidence_id} "
                        "does not match raw_text offsets."
                    )

        obligation_ids = [
            item.obligation_id
            for item in self.obligations
        ]

        if len(obligation_ids) != len(
            set(obligation_ids)
        ):
            raise ValueError(
                "obligation_id values must be unique."
            )

        for obligation in self.obligations:
            if obligation.audience:
                check_ids(
                    obligation
                    .audience
                    .evidence_span_ids,
                    obligation.obligation_id,
                )

            check_ids(
                obligation
                .action
                .evidence_span_ids,
                obligation.obligation_id,
            )

            if obligation.deadline:
                check_ids(
                    obligation
                    .deadline
                    .evidence_span_ids,
                    obligation.obligation_id,
                )

            for occurrence in obligation.event_occurrences:
                check_ids(occurrence.evidence_span_ids, obligation.obligation_id)
                if occurrence.location:
                    check_ids(occurrence.location.evidence_span_ids, obligation.obligation_id)
                if occurrence.audience:
                    check_ids(occurrence.audience.evidence_span_ids, obligation.obligation_id)

            if obligation.amount:
                check_ids(
                    obligation
                    .amount
                    .evidence_span_ids,
                    obligation.obligation_id,
                )

            if obligation.location:
                check_ids(
                    obligation
                    .location
                    .evidence_span_ids,
                    obligation.obligation_id,
                )

            for document in (
                obligation.required_documents
            ):
                check_ids(
                    document.evidence_span_ids,
                    obligation.obligation_id,
                )

            for exception in (
                obligation.exceptions
            ):
                check_ids(
                    exception.evidence_span_ids,
                    obligation.obligation_id,
                )

        for relation in (
            self.temporal_relations
        ):
            check_ids(
                relation.evidence_span_ids,
                "temporal relation",
            )

            if (
                relation.target_notice_id
                == self.notice_id
                and (
                    relation.target_version_id
                    is None
                    or relation.target_version_id
                    == self.version_id
                )
            ):
                raise ValueError(
                    "Temporal relation cannot "
                    "point to itself."
                )

        return self
