from app.verification.service import VerificationService
from app.verification.models import OverallVerdict
# We can use mock objects to unit test VerificationService 
# but a full E2E is better done in integration tests.

def test_verification_service_verdicts():
    from app.verification.verdict import VerdictAggregator
    from app.verification.models import FieldComparisonResult, FieldMatchState
    
    # Happy Path
    assert VerdictAggregator.aggregate({
        "a": FieldComparisonResult(state=FieldMatchState.MATCH)
    }) == OverallVerdict.VERIFIED
    
    # Conflict Path
    assert VerdictAggregator.aggregate({
        "a": FieldComparisonResult(state=FieldMatchState.MATCH),
        "b": FieldComparisonResult(state=FieldMatchState.CONFLICT)
    }) == OverallVerdict.CONFLICT
    
    # Partial Path
    assert VerdictAggregator.aggregate({
        "a": FieldComparisonResult(state=FieldMatchState.MATCH),
        "b": FieldComparisonResult(state=FieldMatchState.INSUFFICIENT_EVIDENCE)
    }) == OverallVerdict.PARTIALLY_VERIFIED
    
    # Insufficient Path
    assert VerdictAggregator.aggregate({
        "a": FieldComparisonResult(state=FieldMatchState.INSUFFICIENT_EVIDENCE)
    }) == OverallVerdict.INSUFFICIENT_EVIDENCE
