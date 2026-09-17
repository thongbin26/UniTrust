from app.verification.abstention import AbstentionPolicy, AbstentionConfig
from app.verification.models import AbstentionReason

def test_abstention_no_retrieval():
    policy = AbstentionPolicy()
    assert policy.check_retrieval([]) == AbstentionReason.NO_RETRIEVAL_EVIDENCE

def test_abstention_no_official_field():
    policy = AbstentionPolicy()
    assert policy.check_official_obligation([]) == AbstentionReason.NO_OFFICIAL_FIELD

def test_abstention_thresholds_disabled():
    policy = AbstentionPolicy(AbstentionConfig(enabled=False, min_score_threshold=0.5))
    assert policy.check_thresholds(0.1) is None

def test_abstention_thresholds_enabled():
    policy = AbstentionPolicy(AbstentionConfig(enabled=True, min_score_threshold=0.5))
    assert policy.check_thresholds(0.1) == AbstentionReason.INSUFFICIENT_FIELD_COVERAGE
