import time
import uuid
from typing import List, Optional

from app.verification.models import (
    VerificationResult, OverallVerdict, AbstentionReason, OfficialProvenance, FieldMatchState,
    FieldComparisonResult, ReceivedFieldProvenance, TypedUserField, DecomposedUserClaim,
)
from app.verification.decomposer import ClaimDecomposer
from app.verification.repository import OfficialStructuredRepository
from app.verification.comparator import FieldComparator
from app.temporal.resolver import TemporalResolver
from app.verification.abstention import AbstentionPolicy
from app.verification.verdict import VerdictAggregator
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.base import RetrievalResult

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

    @staticmethod
    def _unique_evidence_candidates(
        retrieved_results: List[RetrievalResult],
    ) -> List[RetrievalResult]:
        """Collapse chunk results by evidence identity without re-ranking."""
        seen: set[tuple[int, int]] = set()
        unique_candidates = []
        for result in retrieved_results:
            identity = (result.chunk.notice_id, result.chunk.version_id)
            if identity not in seen:
                seen.add(identity)
                unique_candidates.append(result)
        return unique_candidates

    @staticmethod
    def _apply_temporal_safety_gate(
        verdict: OverallVerdict,
        temporal_status,
    ) -> OverallVerdict:
        if temporal_status.name != "SUPERSEDED_OUTDATED":
            return verdict
        if verdict == OverallVerdict.VERIFIED:
            return OverallVerdict.PARTIALLY_VERIFIED
        if verdict == OverallVerdict.CONFLICT:
            return OverallVerdict.INSUFFICIENT_EVIDENCE
        return verdict

    def _evaluate_obligation(
        self,
        claim,
        official_obligation,
        provenance: OfficialProvenance,
    ) -> tuple[dict[str, FieldComparisonResult], int, int, tuple]:
        # Deadlines and amounts only describe an obligation after its action is
        # established. Retrieval similarity alone must not authorize a related
        # but different obligation to verify or contradict those dependent fields.
        official_action = getattr(official_obligation, "action", None)
        if claim.action is None or official_action is None:
            return {}, 0, 0, (("applicability", "UNESTABLISHED"),)

        action_result = FieldComparator.compare_action(
            claim.action.text,
            official_action.action_type,
            normalized_claimed=(
                claim.action.normalized_value
                if isinstance(claim.action.normalized_value, str)
                else None
            ),
            claimed_text=claim.action.raw_text,
        )
        if action_result.state != FieldMatchState.MATCH:
            return {}, 0, 0, (("applicability", "INCOMPATIBLE"),)

        field_results = {"action": action_result}
        canonical_values = {"action": official_action.action_type.value}

        if claim.deadline:
            if official_obligation.deadline and claim.deadline.normalized_value:
                field_results["deadline"] = FieldComparator.compare_deadline(
                    claim.deadline.text,
                    official_obligation.deadline.raw_text,
                    normalized_claimed=(
                        claim.deadline.normalized_value
                        if isinstance(claim.deadline.normalized_value, str)
                        else None
                    ),
                    normalized_official=official_obligation.deadline.normalized,
                    claimed_text=claim.deadline.raw_text,
                )
                canonical_values["deadline"] = FieldComparator._normalize_date(
                    official_obligation.deadline.normalized
                    or official_obligation.deadline.raw_text,
                )
            else:
                field_results["deadline"] = self._insufficient_field(
                    claim.deadline,
                    "No comparable official deadline found.",
                )

        if claim.amount:
            if official_obligation.amount:
                field_results["amount"] = FieldComparator.compare_amount(
                    claim.amount.text,
                    str(official_obligation.amount.value_vnd),
                    normalized_claimed=(
                        claim.amount.normalized_value
                        if isinstance(claim.amount.normalized_value, int)
                        else None
                    ),
                    claimed_text=claim.amount.raw_text,
                )
                canonical_values["amount"] = official_obligation.amount.value_vnd
            else:
                field_results["amount"] = self._insufficient_field(
                    claim.amount,
                    "No official amount found.",
                )

        received_fields = {
            "action": claim.action,
            "deadline": claim.deadline,
            "amount": claim.amount,
        }
        for name, comparison in field_results.items():
            comparison.provenance = provenance
            received = received_fields.get(name)
            if received:
                comparison.received_provenance = self._received_provenance(received)

        comparable_count = sum(
            result.state != FieldMatchState.INSUFFICIENT_EVIDENCE
            for result in field_results.values()
        )
        match_count = sum(
            result.state == FieldMatchState.MATCH
            for result in field_results.values()
        )
        signature = tuple(
            (name, result.state.value, canonical_values.get(name))
            for name, result in sorted(field_results.items())
        )
        return field_results, match_count, comparable_count, signature

    def verify(self, text: str, top_k: int = 5) -> List[VerificationResult]:
        results = []

        # 1. Decomposition
        decomposed_claims = self.decomposer.decompose(text)

        for claim in decomposed_claims:
            understood_fields = self._understood_fields(claim)
            has_supported_field = any((claim.action, claim.deadline, claim.amount))

            # 2. Retrieval
            # Keep raw claim text as the retrieval fallback; normalized values are
            # used only for deterministic field comparison below.
            # Verification must never choose a historical version when the
            # corpus also contains a current version.  Generic search keeps
            # historical chunks for audit/history views; the HybridRetriever
            # exposes this narrow current-evidence view for trust decisions.
            search_current = getattr(self.retriever, "search_current", None)
            if callable(search_current) and isinstance(getattr(self.retriever, "retrievers", None), list):
                retrieved_results = search_current(claim.raw_claim_text, top_k=top_k)
            else:
                # Compatibility for small test/custom retrievers.  Production
                # HybridRetriever always provides search_current().
                retrieved_results = [
                    result
                    for result in self.retriever.search(claim.raw_claim_text, top_k=top_k)
                    if result.chunk.is_latest_version
                ]

            if not has_supported_field:
                results.append(VerificationResult(
                    claim_id=claim.claim_id,
                    raw_claim_text=claim.raw_claim_text,
                    verdict=OverallVerdict.ABSTAINED,
                    abstention_reason=AbstentionReason.UNSUPPORTED_CLAIM_FIELD,
                    understood_fields=understood_fields,
                ))
                continue

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
                    ,understood_fields=understood_fields
                ))
                continue

            unique_candidates = self._unique_evidence_candidates(retrieved_results)
            top_chunk = unique_candidates[0].chunk

            # 3. Official Structured Field Source Lookup
            obligations = self.repository.get_reviewed_official_obligations(
                top_chunk.notice_id,
                top_chunk.version_id,
            )

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

            # 4. Typed Field Comparisons and safe obligation selection.
            evaluated_obligations = [
                self._evaluate_obligation(claim, obligation, provenance)
                for obligation in obligations
            ]
            usable_obligations = [
                evaluation for evaluation in evaluated_obligations
                if evaluation[2] > 0
            ]

            # 5. Temporal Resolution
            temporal_status = self.temporal_resolver.resolve_validity(top_chunk.notice_id, top_chunk.version_id)

            # 6. Coverage / Abstention Policy
            reason = self.abstention_policy.check_official_obligation(obligations)
            if not reason and not usable_obligations:
                reason = AbstentionReason.NO_OFFICIAL_FIELD

            if reason:
                # If there's an abstention reason due to coverage, we override
                results.append(VerificationResult(
                    claim_id=claim.claim_id,
                    raw_claim_text=claim.raw_claim_text,
                    verdict=OverallVerdict.ABSTAINED,
                    abstention_reason=reason,
                    primary_provenance=provenance,
                    temporal_status=temporal_status
                    ,understood_fields=understood_fields
                ))
                continue

            highest_match_count = max(evaluation[1] for evaluation in usable_obligations)
            tied_obligations = [
                evaluation for evaluation in usable_obligations
                if evaluation[1] == highest_match_count
            ]
            if len({evaluation[3] for evaluation in tied_obligations}) > 1:
                results.append(VerificationResult(
                    claim_id=claim.claim_id,
                    raw_claim_text=claim.raw_claim_text,
                    verdict=OverallVerdict.ABSTAINED,
                    abstention_reason=AbstentionReason.AMBIGUOUS_OFFICIAL_EVIDENCE,
                    temporal_status=temporal_status,
                    understood_fields=understood_fields,
                ))
                continue

            field_results = tied_obligations[0][0]

            # 7. Deterministic Verdict Aggregation
            verdict = self._apply_temporal_safety_gate(
                VerdictAggregator.aggregate(field_results),
                temporal_status,
            )

            # 8. Structured Explanation
            results.append(VerificationResult(
                claim_id=claim.claim_id,
                raw_claim_text=claim.raw_claim_text,
                verdict=verdict,
                temporal_status=temporal_status,
                field_results=field_results,
                primary_provenance=provenance
                ,understood_fields=understood_fields
            ))

        return results

    @staticmethod
    def _understood_fields(claim: DecomposedUserClaim) -> dict[str, TypedUserField | list[TypedUserField]]:
        fields: dict[str, TypedUserField | list[TypedUserField]] = {}
        for name in ("audience", "action", "object_hint", "deadline", "amount", "location"):
            value = getattr(claim, name)
            if value is not None:
                fields[name] = value
        for name in ("required_documents", "exceptions"):
            values = getattr(claim, name)
            if values:
                fields[name] = values
        return fields
