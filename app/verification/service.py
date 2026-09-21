import time
import uuid
from typing import List, Optional

from app.verification.models import (
    VerificationResult, OverallVerdict, AbstentionReason, OfficialProvenance, FieldMatchState,
    FieldComparisonResult, ReceivedFieldProvenance, TypedUserField,
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

    @staticmethod
    def _received_provenance(field: TypedUserField) -> ReceivedFieldProvenance:
        return ReceivedFieldProvenance(
            text=field.raw_text or field.text,
            start_char=field.start_char,
            end_char=field.end_char,
            normalized_value=field.normalized_value,
            extraction_method=field.extraction_method,
        )

    @staticmethod
    def _insufficient_field(field: TypedUserField, explanation: str) -> FieldComparisonResult:
        return FieldComparisonResult(
            state=FieldMatchState.INSUFFICIENT_EVIDENCE,
            claimed_text=field.raw_text or field.text,
            explanation=explanation,
        )

    def verify(self, text: str, top_k: int = 5) -> List[VerificationResult]:
        results = []

        # 1. Decomposition
        decomposed_claims = self.decomposer.decompose(text)

        for claim in decomposed_claims:
            # 2. Retrieval
            # Keep raw claim text as the retrieval fallback; normalized values are
            # used only for deterministic field comparison below.
            retrieved_results = self.retriever.search(claim.raw_claim_text, top_k=top_k)

            # Hard early exit for NO_RETRIEVAL_EVIDENCE
            # Convert RetrievalResult list back to RetrievalChunk list for abstention_policy (which expects chunks or results)
            retrieved_chunks = [r.chunk for r in retrieved_results]
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
            best_obligation = None
            best_match_count = -1
            best_field_results = {}

            for official_obligation in obligations:
                current_field_results = {}
                if claim.action:
                    current_field_results["action"] = FieldComparator.compare_action(
                        claim.action.text,
                        official_obligation.action.action_type,
                        normalized_claimed=(
                            claim.action.normalized_value
                            if isinstance(claim.action.normalized_value, str)
                            else None
                        ),
                        claimed_text=claim.action.raw_text,
                    )

                if claim.deadline:
                    if official_obligation.deadline and claim.deadline.normalized_value:
                        current_field_results["deadline"] = FieldComparator.compare_deadline(
                            claim.deadline.text,
                            official_obligation.deadline.raw_text,
                            normalized_claimed=(
                                claim.deadline.normalized_value
                                if isinstance(claim.deadline.normalized_value, str)
                                else None
                            ),
                            claimed_text=claim.deadline.raw_text,
                        )
                    else:
                        current_field_results["deadline"] = self._insufficient_field(
                            claim.deadline,
                            "No comparable official deadline found.",
                        )

                if claim.amount:
                    if official_obligation.amount:
                        current_field_results["amount"] = FieldComparator.compare_amount(
                            claim.amount.text,
                            str(official_obligation.amount.value_vnd),
                            normalized_claimed=(
                                claim.amount.normalized_value
                                if isinstance(claim.amount.normalized_value, int)
                                else None
                            ),
                            claimed_text=claim.amount.raw_text,
                        )
                    else:
                        current_field_results["amount"] = self._insufficient_field(
                            claim.amount,
                            "No official amount found.",
                        )

                received_fields = {
                    "action": claim.action,
                    "deadline": claim.deadline,
                    "amount": claim.amount,
                }
                for name, comparison in current_field_results.items():
                    comparison.provenance = provenance
                    received = received_fields.get(name)
                    if received:
                        comparison.received_provenance = self._received_provenance(received)

                match_count = sum(1 for r in current_field_results.values() if r.state == FieldMatchState.MATCH)
                if match_count > best_match_count:
                    best_match_count = match_count
                    best_obligation = official_obligation
                    best_field_results = current_field_results

            field_results = best_field_results

            # 5. Temporal Resolution
            temporal_status = self.temporal_resolver.resolve_validity(top_chunk.notice_id, top_chunk.version_id)

            # 6. Coverage / Abstention Policy
            reason = self.abstention_policy.check_official_obligation(obligations)

            if not field_results and not reason:
                reason = AbstentionReason.UNSUPPORTED_CLAIM_FIELD

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
