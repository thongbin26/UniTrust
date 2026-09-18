# ui_translations.py
# Maps backend canonical enums to Vietnamese presentation strings

TRUST_STATE_VI = {
    "VERIFIED": "Đã xác minh",
    "PARTIALLY_VERIFIED": "Xác minh một phần",
    "CONFLICT": "Có mâu thuẫn",
    "INSUFFICIENT_EVIDENCE": "Chưa đủ bằng chứng"
}

TEMPORAL_STATE_VI = {
    "CURRENT": "Phiên bản hiện hành",
    "SUPERSEDED_OUTDATED": "Đã bị thay thế / lỗi thời",
    "UNKNOWN": "Chưa xác định phiên bản"
}

APPLICABILITY_VI = {
    "APPLIES": "Áp dụng cho bạn",
    "DOES_NOT_APPLY": "Không áp dụng",
    "UNKNOWN": "Chưa đủ thông tin để xác định"
}

ABSTENTION_REASONS_VI = {
    "NO_OFFICIAL_FIELD": "Chưa có bằng chứng chính thức cho loại thông tin này.",
    "NO_EVIDENCE": "Không tìm thấy thông báo chính thức liên quan.",
    "AMBIGUOUS_EVIDENCE": "Bằng chứng chưa đủ rõ ràng để kết luận.",
    "PARTIAL_MATCH": "Nội dung khớp một phần nhưng còn thiếu thông tin."
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

def get_field_name_vi(field: str) -> str:
    return FIELD_NAMES_VI.get(field, field.title())

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
