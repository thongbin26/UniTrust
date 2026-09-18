DEMO_CASES = [
    {
        "case_id": "case_a_supported",
        "label": "Example 1: Verified (Real-Source Derived)",
        "claim_text": "Sinh viên khóa 2022 ngành CNTT ký tên theo danh sách lớp và nộp 01 ảnh thẻ 2x3 trước 16h00 ngày 26/06/2026.",
        "purpose": "Showcase a fully verified claim matching official reviewed evidence.",
        "is_synthetic": False,
        "source_notice_id": 13,
        "source_version_id": 13
    },
    {
        "case_id": "case_b_conflict",
        "label": "Example 2: Wrong Deadline (SYNTHETIC DEMO MUTATION DERIVED FROM REVIEWED DUT EVIDENCE)",
        "claim_text": "Sinh viên khóa 2022 ngành CNTT ký tên theo danh sách lớp và nộp 01 ảnh thẻ 2x3 trước 16h00 ngày 30/06/2026.",
        "purpose": "Showcase conflict detection on a mutated deadline.",
        "is_synthetic": True,
        "source_notice_id": 13,
        "source_version_id": 13
    },
    {
        "case_id": "case_c_unsupported",
        "label": "Example 3: Unsupported (Diagnostic Case)",
        "claim_text": "Đại học yêu cầu sinh viên đi học mặc áo màu đỏ",
        "purpose": "Showcase abstention for unsupported claims.",
        "is_synthetic": True,
        "source_notice_id": None,
        "source_version_id": None
    }
]
