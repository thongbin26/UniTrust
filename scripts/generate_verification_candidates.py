import json
import uuid
from pathlib import Path

from app.models.obligation import CanonicalNoticeAnnotation
from app.models.verification import (
    VerificationBenchmarkClaim,
    ClaimType,
    ExpectedTrustState,
    ExpectedTemporalState,
    ReviewStatus
)

def generate_candidates_for_annotation(annotation: CanonicalNoticeAnnotation) -> list[VerificationBenchmarkClaim]:
    candidates = []
    
    # Process obligations to create valid candidates
    for obligation in annotation.obligations:
        # EXACT_MATCH
        if obligation.action:
            candidates.append(
                VerificationBenchmarkClaim(
                    claim_id=str(uuid.uuid4()),
                    source_notice_id=annotation.notice_id,
                    source_version_id=annotation.version_id,
                    source_evidence_span_ids=obligation.action.evidence_span_ids,
                    claim_text=f"I need to {obligation.action.text}",
                    claim_type=ClaimType.EXACT_MATCH,
                    target_fields=["action"],
                    expected_trust_state=ExpectedTrustState.VERIFIED,
                    expected_temporal_state=ExpectedTemporalState.CURRENT,
                    is_synthetic=False,
                    generation_method="extracted_exact",
                    review_status=ReviewStatus.CANDIDATE
                )
            )
            
            # WRONG_AMOUNT (Only if real payment amount exists)
            if obligation.amount:
                wrong_amount = obligation.amount.value_vnd + 500000
                candidates.append(
                    VerificationBenchmarkClaim(
                        claim_id=str(uuid.uuid4()),
                        source_notice_id=annotation.notice_id,
                        source_version_id=annotation.version_id,
                        source_evidence_span_ids=obligation.amount.evidence_span_ids,
                        claim_text=f"I have to pay {wrong_amount} VND for {obligation.action.text}",
                        claim_type=ClaimType.WRONG_AMOUNT,
                        target_fields=["amount", "action"],
                        expected_trust_state=ExpectedTrustState.CONFLICT,
                        expected_temporal_state=ExpectedTemporalState.CURRENT,
                        mutation_type="amount_increase",
                        is_synthetic=True,
                        generation_method="rule_based",
                        review_status=ReviewStatus.CANDIDATE
                    )
                )
                
            # WRONG_DEADLINE
            if obligation.deadline:
                candidates.append(
                    VerificationBenchmarkClaim(
                        claim_id=str(uuid.uuid4()),
                        source_notice_id=annotation.notice_id,
                        source_version_id=annotation.version_id,
                        source_evidence_span_ids=obligation.deadline.evidence_span_ids,
                        claim_text=f"The deadline for {obligation.action.text} is next year.",
                        claim_type=ClaimType.WRONG_DEADLINE,
                        target_fields=["deadline", "action"],
                        expected_trust_state=ExpectedTrustState.CONFLICT,
                        expected_temporal_state=ExpectedTemporalState.CURRENT,
                        mutation_type="deadline_change",
                        is_synthetic=True,
                        generation_method="rule_based",
                        review_status=ReviewStatus.CANDIDATE
                    )
                )
                
            # WRONG_AUDIENCE
            if obligation.audience and obligation.audience.raw_text:
                candidates.append(
                    VerificationBenchmarkClaim(
                        claim_id=str(uuid.uuid4()),
                        source_notice_id=annotation.notice_id,
                        source_version_id=annotation.version_id,
                        source_evidence_span_ids=obligation.audience.evidence_span_ids,
                        claim_text=f"All students must {obligation.action.text}.",
                        claim_type=ClaimType.WRONG_AUDIENCE,
                        target_fields=["audience", "action"],
                        expected_trust_state=ExpectedTrustState.CONFLICT,
                        expected_temporal_state=ExpectedTemporalState.CURRENT,
                        mutation_type="audience_change",
                        is_synthetic=True,
                        generation_method="rule_based",
                        review_status=ReviewStatus.CANDIDATE
                    )
                )

            # WRONG_LOCATION
            if obligation.location:
                candidates.append(
                    VerificationBenchmarkClaim(
                        claim_id=str(uuid.uuid4()),
                        source_notice_id=annotation.notice_id,
                        source_version_id=annotation.version_id,
                        source_evidence_span_ids=obligation.location.evidence_span_ids,
                        claim_text=f"I must {obligation.action.text} at the incorrect office.",
                        claim_type=ClaimType.WRONG_LOCATION,
                        target_fields=["location", "action"],
                        expected_trust_state=ExpectedTrustState.CONFLICT,
                        expected_temporal_state=ExpectedTemporalState.CURRENT,
                        mutation_type="location_change",
                        is_synthetic=True,
                        generation_method="rule_based",
                        review_status=ReviewStatus.CANDIDATE
                    )
                )
                
            # WRONG_REQUIRED_DOCUMENT
            if obligation.required_documents:
                candidates.append(
                    VerificationBenchmarkClaim(
                        claim_id=str(uuid.uuid4()),
                        source_notice_id=annotation.notice_id,
                        source_version_id=annotation.version_id,
                        source_evidence_span_ids=obligation.required_documents[0].evidence_span_ids,
                        claim_text=f"I must bring a fake document to {obligation.action.text}.",
                        claim_type=ClaimType.WRONG_REQUIRED_DOCUMENT,
                        target_fields=["required_documents", "action"],
                        expected_trust_state=ExpectedTrustState.CONFLICT,
                        expected_temporal_state=ExpectedTemporalState.CURRENT,
                        mutation_type="document_change",
                        is_synthetic=True,
                        generation_method="rule_based",
                        review_status=ReviewStatus.CANDIDATE
                    )
                )

    return candidates

def main():
    annotations_dir = Path("data/annotations/batch_001")
    out_dir = Path("data/benchmark/verification")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = out_dir / "candidates.jsonl"
    
    all_candidates = []
    
    # Process only real reviewed annotations, skip the example fixture
    for file_path in annotations_dir.glob("*.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            annotation = CanonicalNoticeAnnotation(**data)
            candidates = generate_candidates_for_annotation(annotation)
            all_candidates.extend(candidates)
                
    with open(out_path, "w", encoding="utf-8") as f:
        for c in all_candidates:
            f.write(c.model_dump_json() + "\n")
            
    print(f"Generated {len(all_candidates)} candidates at {out_path}")

if __name__ == "__main__":
    main()
