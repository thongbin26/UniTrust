from app.verification.claim_extractor import DeterministicTextClaimExtractor
from app.verification.models import OverallVerdict
from app.verification.structured_ai import OptionalAIExtractorUnavailable
from app.verification.verdict import VerdictAggregator


def test_coordinated_actions_become_independent_grounded_claims():
    text = "K26 cần đăng ký kiểm tra xếp lớp trước ngày 18/09/2026 và đóng 450.000 đồng."
    claims = DeterministicTextClaimExtractor().extract(text)
    assert len(claims) == 2
    assert [claim.action.normalized_value for claim in claims] == ["register", "pay"]
    assert text[claims[0].start_char:claims[0].end_char] == claims[0].raw_claim_text
    assert text[claims[1].start_char:claims[1].end_char] == claims[1].raw_claim_text
    assert claims[0].deadline.normalized_value == "2026-09-18"
    assert claims[1].amount.normalized_value == 450000
    assert claims[0].audience is not None
    assert claims[0].audience.normalized_value == "K26"


def test_message_aggregation_preserves_mixed_claim_safety():
    assert VerdictAggregator.aggregate_claim_verdicts([
        OverallVerdict.VERIFIED, OverallVerdict.INSUFFICIENT_EVIDENCE,
    ]) == OverallVerdict.PARTIALLY_VERIFIED
    assert VerdictAggregator.aggregate_claim_verdicts([
        OverallVerdict.VERIFIED, OverallVerdict.CONFLICT,
    ]) == OverallVerdict.CONFLICT
    assert VerdictAggregator.aggregate_claim_verdicts([
        OverallVerdict.PARTIALLY_VERIFIED,
        OverallVerdict.INSUFFICIENT_EVIDENCE,
        OverallVerdict.INSUFFICIENT_EVIDENCE,
    ]) == OverallVerdict.PARTIALLY_VERIFIED


def test_optional_ai_boundary_is_offline_safe():
    try:
        OptionalAIExtractorUnavailable().extract("Nộp hồ sơ")
    except RuntimeError as exc:
        assert str(exc) == "AI_UNAVAILABLE"
    else:
        raise AssertionError("offline placeholder must not fabricate AI output")


def test_three_claims_keep_modifier_scope_and_order():
    text = "K26 cần đăng ký kiểm tra xếp lớp trước 18/09, đóng 450.000 đồng và nộp CCCD."
    claims = DeterministicTextClaimExtractor().extract(text)
    assert len(claims) == 3
    assert [claim.action.normalized_value for claim in claims] == ["register", "pay", "submit"]
    assert claims[0].deadline is not None and claims[0].deadline.normalized_value is None
    assert claims[1].deadline is None and claims[1].amount.normalized_value == 450000
    assert claims[2].required_documents == []  # no unsupported document inference without a trigger


def test_two_audiences_stay_with_their_own_clauses():
    text = "Sinh viên K26 đăng ký kiểm tra trước 18/09 và sinh viên K25 nộp hồ sơ trước 20/09."
    claims = DeterministicTextClaimExtractor().extract(text)
    assert len(claims) == 2
    assert [claim.audience.normalized_value for claim in claims] == ["K26", "K25"]


def test_bare_dong_never_becomes_payment():
    claim = DeterministicTextClaimExtractor().extract("Sinh viên đóng góp ý kiến.")[0]
    assert claim.action is None
