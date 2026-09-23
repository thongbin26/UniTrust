from app.models.obligation import (
    ActionType,
    ActionValue,
    DeadlineValue,
    MoneyValue,
    StudentObligation,
    TemporalPrecision,
)
from app.retrieval.base import RetrievalChunk, RetrievalResult
from app.temporal.models import TemporalValidity
from app.verification.abstention import AbstentionPolicy
from app.verification.decomposer import ClaimDecomposer
from app.verification.models import AbstentionReason, OverallVerdict
from app.verification.service import VerificationService


def chunk(notice_id, version_id=1, chunk_id=None):
    return RetrievalChunk(
        chunk_id=chunk_id or f"chunk-{notice_id}-{version_id}",
        notice_id=notice_id,
        version_id=version_id,
        source_id="synthetic",
        start_char=0,
        end_char=100,
        text="Synthetic official evidence.",
        title=f"Synthetic notice {notice_id}",
        canonical_url=f"https://example.test/{notice_id}",
        is_latest_version=True,
    )


def result(item, rank):
    return RetrievalResult(chunk=item, rank=rank, score=1.0 / rank, retrieval_method="hybrid_rrf")


def obligation(action=ActionType.PAY, amount=None, suffix=""):
    return StudentObligation(
        obligation_id=f"obligation-{action.value}-{amount}-{suffix}",
        action=ActionValue(action_type=action, text=action.value),
        amount=MoneyValue(raw_text=f"{amount} dong", value_vnd=amount) if amount is not None else None,
    )


def obligation_without_action(amount=None, suffix=""):
    return obligation(amount=amount, suffix=suffix).model_copy(update={"action": None})


def with_deadline(item, value):
    return item.model_copy(update={
        "deadline": DeadlineValue(
            raw_text=value,
            normalized=value,
            precision=TemporalPrecision.DATE,
        )
    })


class StaticRetriever:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def search(self, query, top_k=5):
        self.calls.append((query, top_k))
        return self.results


class ReviewedRepository:
    def __init__(self, obligations_by_identity):
        self.obligations_by_identity = obligations_by_identity

    def get_reviewed_official_obligations(self, notice_id, version_id):
        return self.obligations_by_identity.get((notice_id, version_id), [])


def service(results, obligations_by_identity, temporal=TemporalValidity.CURRENT):
    verified_service = VerificationService(
        StaticRetriever(results),
        ClaimDecomposer(),
        ReviewedRepository(obligations_by_identity),
        AbstentionPolicy(),
    )
    verified_service.temporal_resolver.resolve_validity = lambda *_: temporal
    return verified_service


def test_duplicate_chunks_collapse_to_the_earliest_evidence_candidate():
    first = chunk(1, chunk_id="first-a")
    duplicate = chunk(1, chunk_id="later-a")
    second = chunk(2, chunk_id="first-b")

    candidates = VerificationService._unique_evidence_candidates([
        result(first, 1), result(duplicate, 2), result(second, 3),
    ])

    assert [(item.chunk.notice_id, item.chunk.version_id) for item in candidates] == [(1, 1), (2, 1)]
    assert candidates[0].chunk.chunk_id == "first-a"
    assert candidates[0].rank == 1


def test_unreviewed_top_candidate_does_not_fall_back_to_lower_reviewed_candidate():
    top = chunk(1, chunk_id="top-unreviewed")
    lower = chunk(2, chunk_id="lower-reviewed")
    verified_service = service(
        [result(top, 1), result(lower, 2)],
        {(2, 1): [obligation()]},
    )

    verified = verified_service.verify("Sinh viên cần đóng học phí.")[0]

    assert verified.verdict == OverallVerdict.ABSTAINED
    assert verified.abstention_reason == AbstentionReason.NO_OFFICIAL_FIELD
    assert verified.primary_provenance.notice_id == 1


def test_top_annotation_without_a_comparable_claimed_field_abstains():
    top = chunk(1)
    verified_service = service([result(top, 1)], {(1, 1): [obligation()]})

    verified = verified_service.verify("Mức phí là 450k.")[0]

    assert verified.verdict == OverallVerdict.ABSTAINED
    assert verified.abstention_reason == AbstentionReason.NO_OFFICIAL_FIELD


def test_unique_best_obligation_is_selected():
    top = chunk(1)
    verified_service = service(
        [result(top, 1)],
        {(1, 1): [obligation(amount=450_000, suffix="match"), obligation(amount=650_000, suffix="other")]},
    )

    verified = verified_service.verify("Sinh viên cần đóng học phí với mức 450k.")[0]

    assert verified.verdict == OverallVerdict.VERIFIED
    assert verified.field_results["amount"].official_text == "450000"


def test_equivalent_obligation_tie_remains_safe():
    top = chunk(1)
    verified_service = service(
        [result(top, 1)],
        {(1, 1): [obligation(amount=450_000, suffix="one"), obligation(amount=450_000, suffix="two")]},
    )

    assert verified_service.verify("Sinh viên cần đóng học phí với mức 450k.")[0].verdict == OverallVerdict.VERIFIED


def test_materially_different_obligation_tie_abstains():
    top = chunk(1)
    verified_service = service(
        [result(top, 1)],
        {(1, 1): [
            obligation(ActionType.PAY, 450_000, "payment"),
            obligation(ActionType.PAY, 550_000, "other-payment"),
        ]},
    )

    verified = verified_service.verify("Sinh viên cần đóng học phí với mức 650k.")[0]

    assert verified.verdict == OverallVerdict.ABSTAINED
    assert verified.abstention_reason == AbstentionReason.AMBIGUOUS_OFFICIAL_EVIDENCE
    assert not verified.field_results


def test_explicit_action_mismatch_cannot_authorize_dependent_conflicts():
    top = chunk(1)
    official = with_deadline(obligation(ActionType.SUBMIT), "2026-09-10")
    verified_service = service([result(top, 1)], {(1, 1): [official]})

    verified = verified_service.verify(
        "Sinh viên đóng học phí 450.000 đồng trước ngày 30/09/2026."
    )[0]

    assert verified.verdict == OverallVerdict.ABSTAINED
    assert verified.abstention_reason == AbstentionReason.NO_OFFICIAL_FIELD
    assert not verified.field_results


def test_degraded_ocr_without_action_cannot_authorize_deadline_conflict():
    top = chunk(1)
    official = with_deadline(obligation(ActionType.SUBMIT), "2026-09-10")
    verified_service = service([result(top, 1)], {(1, 1): [official]})
    text = (
        "THÔNG BÁO HOC PHÍ\n"
        "Sinh viên K26 đóng hc phí 450.000 đồng.\n"
        "Han cui: 30/09/2026\n"
        "Liên h: Phòng Công tác Sinh viên - DUT"
    )

    verified = verified_service.verify(text)[0]

    assert ClaimDecomposer().decompose(text)[0].action is None
    assert verified.verdict == OverallVerdict.ABSTAINED
    assert verified.abstention_reason == AbstentionReason.NO_OFFICIAL_FIELD
    assert not verified.field_results


def test_same_action_deadline_conflict_remains_authoritative():
    top = chunk(1)
    official = with_deadline(obligation(ActionType.PAY), "2026-09-10")
    verified_service = service([result(top, 1)], {(1, 1): [official]})

    verified = verified_service.verify(
        "Sinh viên đóng học phí trước ngày 30/09/2026."
    )[0]

    assert verified.verdict == OverallVerdict.CONFLICT
    assert verified.field_results["action"].state.value == "MATCH"
    assert verified.field_results["deadline"].state.value == "CONFLICT"


def test_same_action_fields_still_verify():
    top = chunk(1)
    official = with_deadline(obligation(ActionType.PAY, 450_000), "2026-09-30")
    verified_service = service([result(top, 1)], {(1, 1): [official]})

    verified = verified_service.verify(
        "Sinh viên đóng học phí 450.000 đồng trước ngày 30/09/2026."
    )[0]

    assert verified.verdict == OverallVerdict.VERIFIED
    assert all(item.state.value == "MATCH" for item in verified.field_results.values())


def test_missing_official_action_cannot_authorize_deadline_conflict():
    top = chunk(1)
    official = with_deadline(obligation_without_action(), "2026-09-10")
    verified_service = service([result(top, 1)], {(1, 1): [official]})

    verified = verified_service.verify(
        "Sinh viên đóng học phí trước ngày 30/09/2026."
    )[0]

    assert verified.verdict == OverallVerdict.ABSTAINED
    assert verified.abstention_reason == AbstentionReason.NO_OFFICIAL_FIELD
    assert not verified.field_results


def test_missing_actions_on_both_sides_cannot_authorize_deadline_conflict():
    top = chunk(1)
    official = with_deadline(obligation_without_action(), "2026-09-10")
    verified_service = service([result(top, 1)], {(1, 1): [official]})

    verified = verified_service.verify("Hạn cuối: 30/09/2026.")[0]

    assert verified.verdict == OverallVerdict.ABSTAINED
    assert verified.abstention_reason == AbstentionReason.NO_OFFICIAL_FIELD
    assert not verified.field_results


def test_inapplicable_top_candidate_does_not_fall_back_to_lower_candidate():
    top = chunk(1, chunk_id="top-submit")
    lower = chunk(2, chunk_id="lower-pay")
    verified_service = service(
        [result(top, 1), result(lower, 2)],
        {
            (1, 1): [obligation(ActionType.SUBMIT)],
            (2, 1): [obligation(ActionType.PAY)],
        },
    )

    verified = verified_service.verify("Sinh viên đóng học phí.")[0]

    assert verified.verdict == OverallVerdict.ABSTAINED
    assert verified.abstention_reason == AbstentionReason.NO_OFFICIAL_FIELD
    assert verified.primary_provenance.notice_id == 1
    assert not verified.field_results


def test_outdated_verified_is_temporally_gated_but_preserves_field_match():
    top = chunk(1)
    verified_service = service(
        [result(top, 1)],
        {(1, 1): [obligation()]},
        TemporalValidity.SUPERSEDED_OUTDATED,
    )

    verified = verified_service.verify("Sinh viên cần đóng học phí.")[0]

    assert verified.verdict == OverallVerdict.PARTIALLY_VERIFIED
    assert verified.temporal_status == TemporalValidity.SUPERSEDED_OUTDATED
    assert verified.field_results["action"].state.value == "MATCH"


def test_outdated_conflict_becomes_insufficient_evidence():
    top = chunk(1)
    verified_service = service(
        [result(top, 1)],
        {(1, 1): [with_deadline(obligation(), "2026-09-10")]},
        TemporalValidity.SUPERSEDED_OUTDATED,
    )

    verified = verified_service.verify(
        "Sinh viên đóng học phí trước ngày 30/09/2026."
    )[0]

    assert verified.verdict == OverallVerdict.INSUFFICIENT_EVIDENCE
    assert verified.field_results["action"].state.value == "MATCH"
    assert verified.field_results["deadline"].state.value == "CONFLICT"


def test_current_and_unknown_do_not_change_the_raw_aggregate():
    top = chunk(1)
    for temporal in (TemporalValidity.CURRENT, TemporalValidity.UNKNOWN):
        verified_service = service([result(top, 1)], {(1, 1): [obligation()]}, temporal)
        verified = verified_service.verify("Sinh viên cần đóng học phí.")[0]
        assert verified.verdict == OverallVerdict.VERIFIED
        assert verified.temporal_status == temporal
