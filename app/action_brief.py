"""Deterministic, evidence-backed student action briefs."""
from pydantic import BaseModel, Field

from app.actionability import resolve_actionability
from app.models.obligation import StudentObligation


UNKNOWN = "Chưa xác định từ nguồn chính thức."


class ActionBrief(BaseModel):
    notice_id: int
    version_id: int
    obligation_id: str
    headline: str
    applies_to_user: str
    applicability_reason: str
    action: str
    deadline: str | None = None
    deadline_status: str
    amount_vnd: int | None = None
    location: str | None = None
    required_documents: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    canonical_url: str | None = None


def build_action_brief(*, notice_id: int, version_id: int, headline: str, obligation: StudentObligation, applies_to_user: str, applicability_reason: str, canonical_url: str | None) -> ActionBrief:
    missing: list[str] = []
    if obligation.deadline is None:
        missing.append("Hạn chót")
    if obligation.amount is None:
        missing.append("Số tiền")
    if obligation.location is None:
        missing.append("Địa điểm")
    if not obligation.required_documents:
        missing.append("Hồ sơ cần chuẩn bị")
    return ActionBrief(
        notice_id=notice_id, version_id=version_id, obligation_id=obligation.obligation_id,
        headline=headline, applies_to_user=applies_to_user, applicability_reason=applicability_reason,
        action=obligation.action.text,
        deadline=obligation.deadline.raw_text if obligation.deadline else None,
        deadline_status=resolve_actionability(deadline=obligation.deadline).value,
        amount_vnd=obligation.amount.value_vnd if obligation.amount else None,
        location=obligation.location.text if obligation.location else None,
        required_documents=[item.text for item in obligation.required_documents],
        exceptions=[item.text for item in obligation.exceptions], missing_information=missing,
        canonical_url=canonical_url,
    )
