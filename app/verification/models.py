from enum import StrEnum
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal
from app.temporal.models import TemporalValidity

class FieldMatchState(StrEnum):
    MATCH = "MATCH"
    CONFLICT = "CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_CLAIMED = "NOT_CLAIMED"

class AbstentionReason(StrEnum):
    NO_RETRIEVAL_EVIDENCE = "NO_RETRIEVAL_EVIDENCE"
    NO_OFFICIAL_FIELD = "NO_OFFICIAL_FIELD"
    INSUFFICIENT_FIELD_COVERAGE = "INSUFFICIENT_FIELD_COVERAGE"
    UNSUPPORTED_CLAIM_FIELD = "UNSUPPORTED_CLAIM_FIELD"
    AMBIGUOUS_OFFICIAL_EVIDENCE = "AMBIGUOUS_OFFICIAL_EVIDENCE"
    TEMPORAL_UNCERTAINTY = "TEMPORAL_UNCERTAINTY"

class OverallVerdict(StrEnum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    CONFLICT = "CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ABSTAINED = "ABSTAINED"

class TypedUserField(BaseModel):
    text: str
    start_char: int
    end_char: int
    raw_text: Optional[str] = None
    normalized_value: str | int | None = None
    extraction_method: Literal["deterministic"] = "deterministic"

    def model_post_init(self, __context: Any) -> None:
        if self.raw_text is None:
            self.raw_text = self.text
        elif self.raw_text != self.text:
            raise ValueError("raw_text must equal the exact grounded text")

class DecomposedUserClaim(BaseModel):
    claim_id: str
    raw_claim_text: str
    start_char: int
    end_char: int
    normalized_text: Optional[str] = None
    
    action: Optional[TypedUserField] = None
    deadline: Optional[TypedUserField] = None
    amount: Optional[TypedUserField] = None
    audience: Optional[TypedUserField] = None
    location: Optional[TypedUserField] = None
    required_documents: List[TypedUserField] = Field(default_factory=list)
    exceptions: List[TypedUserField] = Field(default_factory=list)

class OfficialProvenance(BaseModel):
    chunk_id: str
    notice_id: int
    version_id: int
    source_id: str
    canonical_url: Optional[str] = None
    title: str
    exact_chunk_text: str
    publication_date: Optional[str] = None
    is_latest_version: bool = False

class FieldComparisonResult(BaseModel):
    state: FieldMatchState
    claimed_text: Optional[str] = None
    official_text: Optional[str] = None
    explanation: str = ""
    provenance: Optional[OfficialProvenance] = None

class VerificationResult(BaseModel):
    claim_id: str
    raw_claim_text: str
    verdict: OverallVerdict
    abstention_reason: Optional[AbstentionReason] = None
    temporal_status: Optional[TemporalValidity] = None
    field_results: dict[str, FieldComparisonResult] = Field(default_factory=dict)
    primary_provenance: Optional[OfficialProvenance] = None
