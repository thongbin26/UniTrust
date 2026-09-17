from datetime import datetime
from app.verification.models import FieldComparisonResult, FieldMatchState
from app.models.obligation import StudentObligation, ActionType

class FieldComparator:
    @staticmethod
    def _normalize_date(text: str) -> str:
        import re
        # Check ISO first
        match_iso = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
        if match_iso:
            return f"{match_iso.group(1)}-{match_iso.group(2)}-{match_iso.group(3)}"
            
        # Check DD/MM/YYYY
        text = text.replace("-", "/")
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
        if match:
            d, m, y = match.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}"
        
        return text

    @staticmethod
    def _normalize_amount(text: str) -> int:
        clean_str = "".join(c for c in text if c.isdigit())
        if clean_str:
            return int(clean_str)
        return -1

    @staticmethod
    def compare_deadline(claimed: str, official: str) -> FieldComparisonResult:
        norm_claim = FieldComparator._normalize_date(claimed)
        norm_off = FieldComparator._normalize_date(official)
        
        if norm_claim == norm_off and norm_claim != claimed: # valid parse
            return FieldComparisonResult(
                state=FieldMatchState.MATCH,
                claimed_text=claimed,
                official_text=official,
                explanation=f"Claimed deadline {claimed} matches official deadline {official}."
            )
        else:
            return FieldComparisonResult(
                state=FieldMatchState.CONFLICT,
                claimed_text=claimed,
                official_text=official,
                explanation=f"Claimed deadline {claimed} conflicts with official deadline {official}."
            )

    @staticmethod
    def compare_amount(claimed: str, official: str) -> FieldComparisonResult:
        c_amt = FieldComparator._normalize_amount(claimed)
        o_amt = FieldComparator._normalize_amount(official)
        
        if c_amt == o_amt and c_amt >= 0:
            return FieldComparisonResult(
                state=FieldMatchState.MATCH,
                claimed_text=claimed,
                official_text=official,
                explanation=f"Claimed amount {claimed} matches official amount {official}."
            )
        else:
            return FieldComparisonResult(
                state=FieldMatchState.CONFLICT,
                claimed_text=claimed,
                official_text=official,
                explanation=f"Claimed amount {claimed} conflicts with official amount {official}."
            )
            
    @staticmethod
    def compare_action(claimed: str, official_action: ActionType) -> FieldComparisonResult:
        # A simple text matching to canonical action type.
        cl = claimed.lower()
        matched = False
        if official_action == ActionType.PAY and "đóng" in cl:
            matched = True
        elif official_action == ActionType.REGISTER and "đăng ký" in cl:
            matched = True
        elif official_action == ActionType.SUBMIT and "nộp" in cl:
            matched = True
            
        if matched:
            return FieldComparisonResult(
                state=FieldMatchState.MATCH,
                claimed_text=claimed,
                official_text=official_action.value,
                explanation=f"Claimed action matches official action {official_action.value}."
            )
        else:
            return FieldComparisonResult(
                state=FieldMatchState.CONFLICT,
                claimed_text=claimed,
                official_text=official_action.value,
                explanation=f"Claimed action conflicts with official action {official_action.value}."
            )
            
    @staticmethod
    def compare_audience(claimed: str, official_all: bool, official_faculties: list[str]) -> FieldComparisonResult:
        # Very simple check
        if official_all:
            return FieldComparisonResult(
                state=FieldMatchState.MATCH,
                claimed_text=claimed,
                official_text="All Students",
                explanation="Notice applies to all students."
            )
        # Unsupported audience
        return FieldComparisonResult(
            state=FieldMatchState.INSUFFICIENT_EVIDENCE,
            claimed_text=claimed,
            official_text="Limited Audience",
            explanation=f"Cannot confidently match claimed audience {claimed} against official audience."
        )

    @staticmethod
    def compare_location(claimed: str, official: str) -> FieldComparisonResult:
        if "http" in claimed and "http" not in official:
            return FieldComparisonResult(
                state=FieldMatchState.CONFLICT,
                claimed_text=claimed,
                official_text=official,
                explanation="URL is not a physical location."
            )
        if claimed.strip().lower() == official.strip().lower():
            return FieldComparisonResult(
                state=FieldMatchState.MATCH,
                claimed_text=claimed,
                official_text=official,
                explanation="Location matches."
            )
        return FieldComparisonResult(
            state=FieldMatchState.CONFLICT,
            claimed_text=claimed,
            official_text=official,
            explanation="Location conflicts."
        )
