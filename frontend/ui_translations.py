from datetime import datetime
import re

# Maps backend canonical enums to Vietnamese presentation strings

TRUST_STATE_VI = {
    "VERIFIED": "Đã xác minh",
    "PARTIALLY_VERIFIED": "Xác minh một phần",
    "CONFLICT": "Có thông tin mâu thuẫn",
    "INSUFFICIENT_EVIDENCE": "Chưa đủ bằng chứng"
}

TEMPORAL_STATE_VI = {
    "CURRENT": "Phiên bản hiện hành",
    "SUPERSEDED_OUTDATED": "Đã bị thay thế / lỗi thời",
    "UNKNOWN": "Chưa xác định phiên bản"
}

APPLICABILITY_VI = {
    "APPLIES": "Có thể áp dụng cho bạn",
    "DOES_NOT_APPLY": "Không áp dụng theo hồ sơ hiện tại",
    "UNKNOWN": "Chưa đủ thông tin để xác định"
}

ABSTENTION_REASONS_VI = {
    "NO_RETRIEVAL_EVIDENCE": "Không tìm thấy thông báo chính thức liên quan.",
    "NO_OFFICIAL_FIELD": "Chưa tìm thấy bằng chứng chính thức đủ phù hợp để đối chiếu với nội dung này.",
    "INSUFFICIENT_FIELD_COVERAGE": "Nguồn hiện có chưa bao quát đủ các chi tiết cần kiểm tra.",
    "UNSUPPORTED_CLAIM_FIELD": "Nội dung này nằm ngoài các trường thông tin hiện được đối chiếu.",
    "AMBIGUOUS_OFFICIAL_EVIDENCE": "Bằng chứng chính thức chưa đủ rõ ràng để kết luận.",
    "TEMPORAL_UNCERTAINTY": "Chưa xác định chắc chắn phiên bản thông báo đang có hiệu lực.",
}

FIELD_STATE_VI = {
    "MATCH": "Khớp với nguồn chính thức",
    "CONFLICT": "Có mâu thuẫn",
    "INSUFFICIENT_EVIDENCE": "Chưa đủ bằng chứng",
    "NOT_CLAIMED": "Không có trong nội dung cần kiểm tra",
}

FIELD_NAMES_VI = {
    "audience": "Đối tượng",
    "action": "Việc cần làm",
    "deadline": "Hạn chót",
    "amount": "Số tiền",
    "location": "Địa điểm",
    "required_documents": "Hồ sơ cần chuẩn bị",
    "source": "Nguồn chính thức",
    "publication_date": "Ngày ban hành"
}

SOURCE_NAMES_VI = {
    "dut_academic": "Thông báo đào tạo và khảo thí DUT",
    "dut_ctsv": "Phòng Công tác Sinh viên",
    "dut_it_faculty": "Khoa Công nghệ Thông tin",
    "dut_sv_portal": "Trang Sinh viên DUT",
    "dut_finance": "Thông báo học phí và tài chính DUT",
    "dut_training_quality": "Phòng Đào tạo và Bảo đảm chất lượng",
    "dut_transport_energy_faculty": "Khoa Cơ khí Giao thông và Năng lượng",
}

NOTICE_PRESENTATION_SUFFIX = re.compile(r"\s+(?:Hot|New)\s*$", re.IGNORECASE)

def get_field_name_vi(field: str) -> str:
    return FIELD_NAMES_VI.get(field, field.title())

def get_field_state_vi(state: str) -> str:
    return FIELD_STATE_VI.get(state, "Chưa xác định")

def get_source_name_vi(source_id: str, source_name: str) -> str:
    return SOURCE_NAMES_VI.get(source_id, source_name or "Nguồn chính thức DUT")

def get_notice_title_vi(title: str | None) -> str:
    """Remove source-site visual badges that were flattened into title text."""
    return NOTICE_PRESENTATION_SUFFIX.sub("", str(title or "")).strip()

def format_date_vi(value: str | None) -> str:
    if not value:
        return "Chưa xác định"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    return parsed.strftime("%d/%m/%Y")

def get_trust_state_vi(verdict: str) -> str:
    return TRUST_STATE_VI.get(verdict, verdict)

def get_temporal_state_vi(status: str) -> str:
    return TEMPORAL_STATE_VI.get(status, status)

def get_applicability_vi(status: str) -> str:
    return APPLICABILITY_VI.get(status, status)

def get_abstention_reason_vi(reason: str) -> str:
    if not reason:
        return "Không có"
    return ABSTENTION_REASONS_VI.get(reason, reason)

def get_explanation_vi(verdict: str) -> str:
    if verdict == "VERIFIED":
        return "Thông tin này khớp với bằng chứng chính thức hiện hành."
    elif verdict == "PARTIALLY_VERIFIED":
        return "Một số phần của thông tin khớp, nhưng một số phần khác chưa được xác minh rõ ràng."
    elif verdict == "CONFLICT":
        return "Một hoặc nhiều chi tiết trong nội dung không khớp với thông báo chính thức."
    elif verdict == "INSUFFICIENT_EVIDENCE":
        return "Chưa có đủ bằng chứng chính thống để đưa ra kết luận chắc chắn."
    return ""
