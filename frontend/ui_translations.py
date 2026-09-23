from datetime import datetime
from zoneinfo import ZoneInfo
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
    "SUPERSEDED_OUTDATED": "Đã có phiên bản mới hơn",
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
    "object_hint": "Nội dung",
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

ACTION_VALUES_VI = {
    "submit": "Nộp",
    "register": "Đăng ký",
    "apply": "Ứng tuyển",
    "pay": "Thanh toán",
    "attend": "Tham gia",
    "collect": "Nhận",
    "check": "Kiểm tra",
    "update": "Cập nhật",
    "other": "Thực hiện",
}

ACTIONABILITY_VI = {
    "UPCOMING": "Sắp đến hạn",
    "ACTIVE": "Còn hiệu lực",
    "EXPIRED": "Đã hết hạn",
    "UNKNOWN": "Chưa xác định",
    "NO_DEADLINE": "",
}

URL_FETCH_ERRORS_VI = {
    "INVALID_URL": "Đường link không hợp lệ.",
    "UNSAFE_URL": "Đường link này không thể được truy cập vì lý do an toàn.",
    "FETCH_TIMEOUT": "Trang phản hồi quá chậm. Vui lòng thử lại.",
    "FETCH_FAILED": "Không thể đọc nội dung từ đường link này.",
    "TOO_LARGE": "Nội dung trang vượt quá giới hạn xử lý.",
    "UNSUPPORTED_CONTENT_TYPE": "Loại nội dung của đường link này chưa được hỗ trợ.",
    "EMPTY_CONTENT": "Không tìm thấy nội dung văn bản phù hợp để kiểm chứng.",
    "TOO_MANY_REDIRECTS": "Đường link chuyển hướng quá nhiều lần.",
}

URL_FETCH_WARNINGS_VI = {
    "CONTENT_TRUNCATED": "Nội dung trang quá dài nên hệ thống chỉ sử dụng phần văn bản cần thiết trong giới hạn xử lý.",
}

NOTICE_PRESENTATION_SUFFIX = re.compile(r"\s+(?:Hot|New)\s*$", re.IGNORECASE)

def get_field_name_vi(field: str) -> str:
    return FIELD_NAMES_VI.get(field, field.title())

def get_field_state_vi(state: str) -> str:
    return FIELD_STATE_VI.get(state, "Chưa xác định")


def get_action_value_vi(value: str | None) -> str:
    """Translate canonical action values without altering raw received wording."""
    if value is None:
        return ""
    text = str(value)
    return ACTION_VALUES_VI.get(text.strip().lower(), text)

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


def format_datetime_vi(value: object | None) -> str:
    """Render optional API timestamps in the student's local time safely."""
    if not value:
        return "Chưa có dữ liệu"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return "Chưa có dữ liệu"
        return parsed.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y, %H:%M")
    except (TypeError, ValueError, OverflowError):
        return "Chưa có dữ liệu"


def get_actionability_vi(value: str | None) -> str:
    return ACTIONABILITY_VI.get(str(value or ""), "Chưa xác định")

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

def get_url_fetch_error_vi(code: str | None) -> str:
    return URL_FETCH_ERRORS_VI.get(code, "Không thể đọc nội dung từ đường link này.")

def get_url_fetch_warning_vi(code: str) -> str:
    return URL_FETCH_WARNINGS_VI.get(code, "Trang có một lưu ý khi xử lý nội dung.")

def get_explanation_vi(verdict: str) -> str:
    if verdict == "VERIFIED":
        return "Thông tin này khớp với bằng chứng chính thức hiện hành."
    elif verdict == "PARTIALLY_VERIFIED":
        return "Một số phần của thông tin khớp, nhưng một số phần khác chưa được xác minh rõ ràng."
    elif verdict == "CONFLICT":
        return "Một số thông tin không khớp với bằng chứng chính thức."
    elif verdict == "INSUFFICIENT_EVIDENCE":
        return "Chưa tìm thấy đủ bằng chứng chính thức phù hợp để đưa ra kết luận chắc chắn."
    return ""
