from frontend.verification_presentation import should_render_official_evidence


NOTICE_24_PROVENANCE = {
    "notice_id": 24,
    "title": "THÔNG BÁO NỘP HỒ SƠ XÉT MIỄN, GIẢM HỌC PHÍ",
    "exact_chunk_text": "Nộp hồ sơ trước ngày 10/09/2026.",
    "canonical_url": "https://dut.udn.vn/notice/24",
}


def test_real_abstention_response_hides_retrieved_only_provenance():
    result = {
        "verdict": "INSUFFICIENT_EVIDENCE",
        "abstention_reason": "NO_OFFICIAL_FIELD",
        "field_results": {},
        "primary_provenance": NOTICE_24_PROVENANCE,
    }

    assert should_render_official_evidence(result) is False


def test_image_flow_result_uses_same_provenance_suppression_rule():
    image_result = {
        "verdict": "INSUFFICIENT_EVIDENCE",
        "abstention_reason": "NO_OFFICIAL_FIELD",
        "field_results": {},
        "primary_provenance": NOTICE_24_PROVENANCE,
    }

    assert should_render_official_evidence(image_result) is False


def test_applicable_evidence_verdicts_keep_official_provenance():
    for verdict in ("VERIFIED", "PARTIALLY_VERIFIED", "CONFLICT"):
        assert should_render_official_evidence({
            "verdict": verdict,
            "primary_provenance": NOTICE_24_PROVENANCE,
        }) is True
