DEMO_CASES = [
    {
        "case_id": "case_a_supported",
        "label": "Example 1: Verified (Real-Source Derived)",
        "ui_label": "Ví dụ 1: Thông tin chính xác",
        "claim_text": "Sinh viên khóa 2022 ngành CNTT ký tên theo danh sách lớp và nộp 01 ảnh thẻ 2x3 trước 16h00 ngày 26/06/2026.",
        "purpose": "Showcase a fully verified claim matching official reviewed evidence.",
        "is_synthetic": False,
        "source_notice_id": 13,
        "source_version_id": 13
    },
    {
        "case_id": "case_b_conflict",
        "label": "Example 2: Wrong Deadline (SYNTHETIC DEMO MUTATION DERIVED FROM REVIEWED DUT EVIDENCE)",
        "ui_label": "Ví dụ 2: Sai hạn chót",
        "claim_text": "Sinh viên đăng ký tham gia VEDC 2026 trước ngày 01/07/2026.",
        "purpose": "Showcase conflict detection on a mutated deadline.",
        "is_synthetic": True,
        "source_notice_id": 17,
        "source_version_id": 17
    },
    {
        "case_id": "case_c_unsupported",
        "label": "Example 3: Unsupported (Diagnostic Case)",
        "ui_label": "Ví dụ 3: Chưa đủ bằng chứng",
        "claim_text": "Đại học yêu cầu sinh viên đi học mặc áo màu đỏ",
        "purpose": "Showcase abstention for unsupported claims.",
        "is_synthetic": True,
        "source_notice_id": None,
        "source_version_id": None
    }
]


def get_demo_case(case_id: str | None) -> dict | None:
    """Return a prepared demo fixture by id without adding verification data."""
    return next((case for case in DEMO_CASES if case["case_id"] == case_id), None)


def selected_demo_text(case_id: str | None) -> str:
    """Provide only the ordinary Verify text input for a selected demo case."""
    case = get_demo_case(case_id)
    return case["claim_text"] if case else ""
