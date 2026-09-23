from datetime import date, datetime
from app.verification.models import FieldComparisonResult, FieldMatchState
from app.models.obligation import StudentObligation, ActionType

class FieldComparator:
    @staticmethod
    def _normalize_date(text: str) -> str | None:
        import re
        # Check ISO first
        match_iso = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
        if match_iso:
            try:
                return date.fromisoformat(match_iso.group(0)).isoformat()
            except ValueError:
                return None
            
        # Check DD/MM/YYYY
        text = text.replace("-", "/")
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
        if match:
            d, m, y = match.groups()
            try:
                return date(int(y), int(m), int(d)).isoformat()
            except ValueError:
                return None
        
        return None

    @staticmethod
    def _normalize_amount(text: str) -> int:
        clean_str = "".join(c for c in text if c.isdigit())
        if clean_str:
            return int(clean_str)
        return -1

    @staticmethod
    def compare_deadline(
        claimed: str,
        official: str,
        *,
        normalized_claimed: str | None = None,
        normalized_official: str | None = None,
        claimed_text: str | None = None,
    ) -> FieldComparisonResult:
        norm_claim = normalized_claimed or FieldComparator._normalize_date(claimed)
        # A reviewed normalized official value is authoritative.  Raw official
        # prose remains a fallback only when that structured value is absent.
        norm_off = FieldComparator._normalize_date(
            normalized_official if normalized_official is not None else official,
        )
        display_claim = claimed_text or claimed
        if norm_claim is None or norm_off is None:
            return FieldComparisonResult(
                state=FieldMatchState.INSUFFICIENT_EVIDENCE,
                claimed_text=display_claim,
                official_text=official,
                explanation="Claimed or official deadline is not a valid calendar date.",
            )
        
        if norm_claim == norm_off:
            return FieldComparisonResult(
                state=FieldMatchState.MATCH,
                claimed_text=display_claim,
                official_text=official,
                explanation=f"Claimed deadline {display_claim} matches official deadline {official}."
            )
        else:
            return FieldComparisonResult(
                state=FieldMatchState.CONFLICT,
                claimed_text=display_claim,
                official_text=official,
                explanation=f"Claimed deadline {display_claim} conflicts with official deadline {official}."
            )

    @staticmethod
    def compare_amount(
        claimed: str,
        official: str,
        *,
        normalized_claimed: int | None = None,
        claimed_text: str | None = None,
    ) -> FieldComparisonResult:
        c_amt = normalized_claimed if normalized_claimed is not None else FieldComparator._normalize_amount(claimed)
        o_amt = FieldComparator._normalize_amount(official)
        display_claim = claimed_text or claimed
        
        if c_amt == o_amt and c_amt >= 0:
            return FieldComparisonResult(
                state=FieldMatchState.MATCH,
                claimed_text=display_claim,
                official_text=official,
                explanation=f"Claimed amount {display_claim} matches official amount {official}."
            )
        else:
            return FieldComparisonResult(
                state=FieldMatchState.CONFLICT,
                claimed_text=display_claim,
                official_text=official,
                explanation=f"Claimed amount {display_claim} conflicts with official amount {official}."
            )
            
    @staticmethod
    def compare_action(
        claimed: str,
        official_action: ActionType,
        *,
        normalized_claimed: str | None = None,
        claimed_text: str | None = None,
    ) -> FieldComparisonResult:
        # A simple text matching to canonical action type.
        cl = claimed.lower()
        display_claim = claimed_text or claimed
        matched = False
        if normalized_claimed is not None:
            # An explicit deterministic normalization must not be overridden
            # by a broader raw lexical overlap (for example PAY vs SUBMIT
            # where both phrases happen to contain "nộp").
            matched = normalized_claimed == official_action.value
        elif official_action == ActionType.PAY and "đóng" in cl:
            matched = True
        elif official_action == ActionType.REGISTER and "đăng ký" in cl:
            matched = True
        elif official_action == ActionType.SUBMIT and "nộp" in cl:
            matched = True
            
        if matched:
            return FieldComparisonResult(
                state=FieldMatchState.MATCH,
                claimed_text=display_claim,
                official_text=official_action.value,
                explanation=f"Claimed action matches official action {official_action.value}."
            )
        else:
            return FieldComparisonResult(
                state=FieldMatchState.CONFLICT,
                claimed_text=display_claim,
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
