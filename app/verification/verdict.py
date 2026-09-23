from typing import Dict
from app.verification.models import FieldComparisonResult, FieldMatchState, OverallVerdict

class VerdictAggregator:
    @staticmethod
    def aggregate(field_results: Dict[str, FieldComparisonResult]) -> OverallVerdict:
        if not field_results:
            return OverallVerdict.INSUFFICIENT_EVIDENCE
            
        has_conflict = False
        has_match = False
        has_insufficient = False
        
        for field, result in field_results.items():
            if result.state == FieldMatchState.CONFLICT:
                has_conflict = True
            elif result.state == FieldMatchState.MATCH:
                has_match = True
            elif result.state == FieldMatchState.INSUFFICIENT_EVIDENCE:
                has_insufficient = True
                
        if has_conflict:
            return OverallVerdict.CONFLICT
            
        if has_match and not has_insufficient:
            return OverallVerdict.VERIFIED
            
        if has_match and has_insufficient:
            return OverallVerdict.PARTIALLY_VERIFIED
            
        return OverallVerdict.INSUFFICIENT_EVIDENCE

    @staticmethod
    def aggregate_claim_verdicts(verdicts: list[OverallVerdict]) -> OverallVerdict:
        """Conservative message summary; individual claim verdicts stay primary."""
        public = [OverallVerdict.INSUFFICIENT_EVIDENCE if value == OverallVerdict.ABSTAINED else value for value in verdicts]
        if any(value == OverallVerdict.CONFLICT for value in public):
            return OverallVerdict.CONFLICT
        if public and all(value == OverallVerdict.VERIFIED for value in public):
            return OverallVerdict.VERIFIED
        if any(value in {OverallVerdict.VERIFIED, OverallVerdict.PARTIALLY_VERIFIED} for value in public):
            return OverallVerdict.PARTIALLY_VERIFIED
        return OverallVerdict.INSUFFICIENT_EVIDENCE
