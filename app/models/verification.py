from enum import StrEnum
from pydantic import BaseModel, Field

class ReviewStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    REVIEWED = "REVIEWED"
    GOLD = "GOLD"

class ClaimType(StrEnum):
    EXACT_MATCH = "exact_match"
    CORRECT_PARAPHRASE = "correct_paraphrase"
    WRONG_DEADLINE = "wrong_deadline"
    WRONG_AMOUNT = "wrong_amount"
    WRONG_AUDIENCE = "wrong_audience"
    WRONG_LOCATION = "wrong_location"
    WRONG_REQUIRED_DOCUMENT = "wrong_required_document"
    PARTIALLY_CORRECT = "partially_correct"
    UNSUPPORTED = "unsupported"

class ExpectedTrustState(StrEnum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    CONFLICT = "CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class ExpectedTemporalState(StrEnum):
    CURRENT = "CURRENT"
    OUTDATED = "OUTDATED"

class VerificationBenchmarkClaim(BaseModel):
    claim_id: str
    
    # Provenance
    source_notice_id: int
    source_version_id: int
    source_evidence_span_ids: list[str] = Field(default_factory=list)
    
    claim_text: str
    claim_type: ClaimType
    target_fields: list[str] = Field(default_factory=list)
    
    expected_trust_state: ExpectedTrustState
    expected_temporal_state: ExpectedTemporalState | None = None
    
    # Synthesis tracking
    mutation_type: str | None = None
    is_synthetic: bool = True
    generation_method: str = "rule_based"
    
    # Review workflow
    review_status: ReviewStatus = ReviewStatus.CANDIDATE
    reviewer_id: str | None = None
    notes: str | None = None
