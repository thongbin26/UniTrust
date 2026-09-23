from app.action_brief import UNKNOWN, build_action_brief
from app.models.obligation import ActionType, ActionValue, DeadlineValue, EvidenceBackedText, MoneyValue, StudentObligation, TemporalPrecision


def test_action_brief_uses_only_structured_official_fields():
    obligation = StudentObligation(
        obligation_id="demo", action=ActionValue(action_type=ActionType.PAY, text="đóng học phí"),
        deadline=DeadlineValue(raw_text="30/09/2026", normalized="2026-09-30", precision=TemporalPrecision.DATE),
        amount=MoneyValue(raw_text="450.000 đồng", value_vnd=450000),
        location=EvidenceBackedText(text="Phòng CTSV"),
    )
    brief = build_action_brief(notice_id=1, version_id=1, headline="Học phí", obligation=obligation, applies_to_user="APPLIES", applicability_reason="Profile explicitly matches all required dimensions", canonical_url="https://dut.udn.vn/Thongbao/id/1")
    assert brief.action == "đóng học phí"
    assert brief.amount_vnd == 450000
    assert brief.location == "Phòng CTSV"
    assert "Hồ sơ cần chuẩn bị" in brief.missing_information
    assert "Địa điểm" not in brief.missing_information


def test_action_brief_never_invents_missing_fields():
    obligation = StudentObligation(obligation_id="minimal", action=ActionValue(action_type=ActionType.SUBMIT, text="nộp hồ sơ"))
    brief = build_action_brief(notice_id=1, version_id=1, headline="Thông báo", obligation=obligation, applies_to_user="UNKNOWN", applicability_reason="Ambiguous audience targets", canonical_url=None)
    assert brief.deadline is None
    assert brief.amount_vnd is None
    assert brief.location is None
    assert brief.required_documents == []
    assert brief.missing_information == ["Hạn chót", "Số tiền", "Địa điểm", "Hồ sơ cần chuẩn bị"]
