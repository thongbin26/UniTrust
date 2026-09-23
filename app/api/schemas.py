from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field
from app.verification.models import OverallVerdict, AbstentionReason, OfficialProvenance, FieldMatchState
from app.temporal.models import TemporalValidity
from app.actionability.models import ActionabilityStatus

class VerifyRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The claim text to verify")
    use_llm: bool = Field(default=False, description="Whether to use semantic LLM fallback")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of official chunks to retrieve")


class URLVerifyRequest(BaseModel):
    """API shape only; public-network safety belongs to WebContentFetcher."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(..., min_length=1, description="Public URL containing user-supplied claim text")
    use_llm: bool = Field(default=False, description="Whether to use semantic LLM fallback")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of official chunks to retrieve")

class FieldComparisonResponse(BaseModel):
    state: str # Using str for frontend ease, or enum name
    claimed_text: str
    official_text: Optional[str] = None
    explanation: str
    received_provenance: Optional["ReceivedFieldProvenanceResponse"] = None


class ReceivedFieldProvenanceResponse(BaseModel):
    text: str
    start_char: int
    end_char: int
    normalized_value: str | int | None = None
    extraction_method: str

class VerifyResponseItem(BaseModel):
    claim_id: str
    raw_claim_text: str
    verdict: str
    temporal_status: Optional[str] = None
    abstention_reason: Optional[str] = None
    field_results: Dict[str, FieldComparisonResponse] = {}
    primary_provenance: Optional[OfficialProvenance] = None

class VerifyResponse(BaseModel):
    original_input: str
    results: List[VerifyResponseItem]
    latency_ms: float


class OCRResponse(BaseModel):
    text: str
    engine: str
    warnings: List[str] = Field(default_factory=list)
    mean_confidence: float | None = None


class VerifyImageResponse(VerifyResponse):
    input_type: str = "IMAGE"
    ocr: OCRResponse


class VerifyURLResponse(VerifyResponse):
    """Verification output plus metadata about user-supplied URL content."""

    input_type: str = "URL"
    requested_url: str
    final_url: str
    page_title: str | None = None
    extracted_text: str
    content_type: str
    warnings: List[str] = Field(default_factory=list)

class EvidenceCoverageStatus(BaseModel):
    has_structured_obligations: bool
    structured_coverage: str  # "REVIEWED", "MACHINE", "NONE"

class NoticeListItem(BaseModel):
    notice_id: int
    title: str
    source_name: str
    publication_date: Optional[str]
    has_structured_obligations: bool
    structured_coverage: str

class NoticeSearchIndexItem(BaseModel):
    """Fields used by the evidence browser; search text is stored notice text."""
    notice_id: int
    title: str
    source_id: str
    source_display_name: str
    searchable_text: str

class NoticeVersionChange(BaseModel):
    field_name: str
    old_value: Any
    new_value: Any
    affected_audience: Optional[str] = None

class NoticeChangesResponse(BaseModel):
    has_history: bool
    changes: List[NoticeVersionChange]

class StudentProfile(BaseModel):
    faculty: Optional[str] = None
    major: Optional[str] = None
    cohort: Optional[str] = None
    program: Optional[str] = None

class ObligationApplicability(BaseModel):
    status: str # "APPLIES", "DOES_NOT_APPLY", "UNKNOWN"
    explanation: str

class ForYouObligationItem(BaseModel):
    obligation_id: str
    action_text: str
    deadline: Optional[str]
    required_documents: List[str]
    location: Optional[str]
    applicability: ObligationApplicability
    temporal_status: str # "CURRENT", "SUPERSEDED_OUTDATED", "UNKNOWN"
    actionability_status: ActionabilityStatus
    notice_id: int
    version_id: int
    title: str
    canonical_url: Optional[str]

class ForYouResponse(BaseModel):
    obligations: List[ForYouObligationItem]
