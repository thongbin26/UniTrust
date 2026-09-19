from frontend.evidence_search import normalize_vietnamese, rank_notices


NOTICES = [
    {
        "notice_id": 30,
        "title": "Lịch sinh hoạt công dân đầu khóa",
        "category": "Rèn luyện & công tác sinh viên",
        "searchable_text": "Thông tin chung cho sinh viên.",
    },
    {
        "notice_id": 13,
        "title": "Thông báo xét tốt nghiệp đợt 2 năm 2026",
        "category": "Tốt nghiệp",
        "searchable_text": "Sinh viên hoàn tất hồ sơ xét tốt nghiệp.",
    },
    {
        "notice_id": 26,
        "title": "Đánh giá kết quả rèn luyện học kỳ II",
        "category": "Rèn luyện & công tác sinh viên",
        "searchable_text": "Sinh viên tự đánh giá điểm rèn luyện.",
    },
    {
        "notice_id": 12,
        "title": "Kế hoạch xét tốt nghiệp đợt 2 năm 2026",
        "category": "Tốt nghiệp",
        "searchable_text": "Sinh viên hoàn tất hồ sơ xét tốt nghiệp.",
    },
]


def test_vietnamese_normalization_handles_d_stroke_and_accents():
    assert normalize_vietnamese("ĐIỂM rèn luyện") == "diem ren luyen"
    assert normalize_vietnamese("điểm rèn luyện") == normalize_vietnamese("diem ren luyen")


def test_diem_ren_luyen_prioritizes_directly_related_notice():
    accented = rank_notices(NOTICES, "điểm rèn luyện")
    ascii_query = rank_notices(NOTICES, "diem ren luyen")
    assert [item["notice_id"] for item in accented] == [item["notice_id"] for item in ascii_query]
    assert accented[0]["notice_id"] == 26


def test_tot_nghiep_prioritizes_direct_matches():
    results = rank_notices(NOTICES, "tốt nghiệp")
    assert {item["notice_id"] for item in results[:2]} == {12, 13}
    assert results[-1]["notice_id"] != 30


def test_ranking_is_stable_and_uses_title_then_notice_id_for_ties():
    forward = rank_notices(NOTICES, "tốt nghiệp")
    reverse = rank_notices(list(reversed(NOTICES)), "tốt nghiệp")
    assert [item["notice_id"] for item in forward] == [item["notice_id"] for item in reverse]
    assert [item["notice_id"] for item in forward[:2]] == [12, 13]
