import time
import uuid
from typing import List, Optional

from app.verification.models import (
    VerificationResult, OverallVerdict, AbstentionReason, OfficialProvenance, FieldMatchState, FieldComparisonResult
)
from app.verification.decomposer import ClaimDecomposer
from app.verification.repository import OfficialStructuredRepository
from app.verification.comparator import FieldComparator
from app.temporal.resolver import TemporalResolver
from app.verification.abstention import AbstentionPolicy
from app.verification.verdict import VerdictAggregator
from app.retrieval.hybrid import HybridRetriever

class VerificationService:
    def __init__(self, retriever: HybridRetriever, decomposer: ClaimDecomposer, repository: OfficialStructuredRepository, abstention_policy: AbstentionPolicy):
        self.retriever = retriever
        self.decomposer = decomposer
        self.repository = repository
        self.abstention_policy = abstention_policy
        self.temporal_resolver = TemporalResolver()

    def verify(self, text: str) -> List[VerificationResult]:
        results = []
        
        # 1. Decomposition
        decomposed_claims = self.decomposer.decompose(text)
        
        for claim in decomposed_claims:
            # 2. Retrieval
            retrieved_chunks = self.retriever.retrieve(claim.raw_claim_text, top_k=5)
            
            # Hard early exit for NO_RETRIEVAL_EVIDENCE
            reason = self.abstention_policy.check_retrieval(retrieved_chunks)
            if reason:
                results.append(VerificationResult(
                    claim_id=claim.claim_id,
                    raw_claim_text=claim.raw_claim_text,
                    verdict=OverallVerdict.ABSTAINED,
                    abstention_reason=reason
                ))
                continue
                
            top_chunk = retrieved_chunks[0]
            
            # 3. Official Structured Field Source Lookup
            obligations = self.repository.get_official_obligations(top_chunk.notice_id, top_chunk.version_id)
            
            # Provenance
            provenance = OfficialProvenance(
                chunk_id=top_chunk.chunk_id,
                notice_id=top_chunk.notice_id,
                version_id=top_chunk.version_id,
                source_id=top_chunk.source_id,
                canonical_url=top_chunk.canonical_url,
                title=top_chunk.title,
                exact_chunk_text=top_chunk.text,
                publication_date=str(top_chunk.publication_date) if top_chunk.publication_date else None,
                is_latest_version=top_chunk.is_latest_version
            )

            # 4. Typed Field Comparisons
            field_results = {}
            if obligations:
                official_obligation = obligations[0]
                if claim.action:
                    field_results["action"] = FieldComparator.compare_action(claim.action.text, official_obligation.action.action_type)
                    field_results["action"].provenance = provenance
                
                if claim.deadline:
                    if official_obligation.deadline:
                        field_results["deadline"] = FieldComparator.compare_deadline(claim.deadline.text, official_obligation.deadline.raw_text)
                    else:
                        field_results["deadline"] = FieldComparisonResult(
                            state=FieldMatchState.INSUFFICIENT_EVIDENCE,
                            claimed_text=claim.deadline.text,
                            explanation="No official deadline found."
                        )
                    field_results["deadline"].provenance = provenance

                if claim.amount:
                    if official_obligation.amount:
                        field_results["amount"] = FieldComparator.compare_amount(claim.amount.text, str(official_obligation.amount.value_vnd))
                    else:
                        field_results["amount"] = FieldComparisonResult(
                            state=FieldMatchState.INSUFFICIENT_EVIDENCE,
                            claimed_text=claim.amount.text,
                            explanation="No official amount found."
                        )
                    field_results["amount"].provenance = provenance
            
            # 5. Temporal Resolution
            temporal_status = self.temporal_resolver.resolve_validity(top_chunk.notice_id, top_chunk.version_id)
            
            # 6. Coverage / Abstention Policy
            reason = self.abstention_policy.check_official_obligation(obligations)
            
            if reason:
                # If there's an abstention reason due to coverage, we override
                results.append(VerificationResult(
                    claim_id=claim.claim_id,
                    raw_claim_text=claim.raw_claim_text,
                    verdict=OverallVerdict.ABSTAINED,
                    abstention_reason=reason,
                    primary_provenance=provenance,
                    temporal_status=temporal_status
                ))
                continue

            # 7. Deterministic Verdict Aggregation
            verdict = VerdictAggregator.aggregate(field_results)
            
            # 8. Structured Explanation
            results.append(VerificationResult(
                claim_id=claim.claim_id,
                raw_claim_text=claim.raw_claim_text,
                verdict=verdict,
                temporal_status=temporal_status,
                field_results=field_results,
                primary_provenance=provenance
            ))
            
        return results
