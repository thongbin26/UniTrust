import pytest
from app.models.verification import VerificationBenchmarkClaim, ClaimType, ExpectedTrustState, ExpectedTemporalState, ReviewStatus
from app.models.obligation import CanonicalNoticeAnnotation, StudentObligation, ActionValue, MoneyValue

def test_verification_dataset_schema_validation():
    claim = VerificationBenchmarkClaim(
        claim_id="1",
        source_notice_id=10,
        source_version_id=20,
        source_evidence_span_ids=["ev1"],
        claim_text="Test claim",
        claim_type=ClaimType.EXACT_MATCH,
        target_fields=["action"],
        expected_trust_state=ExpectedTrustState.VERIFIED,
        expected_temporal_state=ExpectedTemporalState.CURRENT,
        is_synthetic=False,
        review_status=ReviewStatus.CANDIDATE
    )
    assert claim.claim_id == "1"
    
def test_synthetic_mutation_provenance():
    claim = VerificationBenchmarkClaim(
        claim_id="2",
        source_notice_id=10,
        source_version_id=20,
        claim_text="Wrong amount",
        claim_type=ClaimType.WRONG_AMOUNT,
        expected_trust_state=ExpectedTrustState.CONFLICT,
        mutation_type="amount_increase",
        is_synthetic=True,
        review_status=ReviewStatus.CANDIDATE
    )
    assert claim.is_synthetic is True
    assert claim.mutation_type == "amount_increase"

def test_prohibition_on_automatic_gold_promotion():
    claim = VerificationBenchmarkClaim(
        claim_id="3",
        source_notice_id=10,
        source_version_id=20,
        claim_text="Test",
        claim_type=ClaimType.EXACT_MATCH,
        expected_trust_state=ExpectedTrustState.VERIFIED,
        is_synthetic=False
    )
    assert claim.review_status == ReviewStatus.CANDIDATE
    assert claim.review_status != ReviewStatus.GOLD

def test_invalid_wrong_amount_prevention():
    # In generate_verification_candidates.py, we only generate WRONG_AMOUNT if obligation.amount exists.
    # The real data has amount=None, so it prevents generating WRONG_AMOUNT.
    from scripts.generate_verification_candidates import generate_candidates_for_annotation
    
    ann = CanonicalNoticeAnnotation(
        annotator_id="A", annotation_status="REVIEWED", notice_id=1, version_id=1,
        source={"source_id": "test", "name": "test"}, title="T", raw_text="R",
        observed_at="2026-09-17T00:00:00Z", url="http", content_hash="hash",
        obligations=[
            StudentObligation(
                obligation_id="1", 
                action=ActionValue(action_type="register", text="Register")
            )
        ]
    )
    
    candidates = generate_candidates_for_annotation(ann)
    types = [c.claim_type for c in candidates]
    
    assert ClaimType.WRONG_AMOUNT not in types
    assert ClaimType.EXACT_MATCH in types
