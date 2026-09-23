from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from frontend.api_client import api_client


ROOT = Path(__file__).resolve().parents[1]


def test_home_is_student_facing_and_has_real_page_links():
    page = AppTest.from_file(ROOT / "frontend/Home.py").run(timeout=20)
    assert not page.exception
    text = "\n".join(element.value for element in page.markdown)
    assert "Kiểm chứng đúng nguồn, an tâm hành động." in text
    assert "Backend URL" not in text
    assert "Chi tiết kỹ thuật" not in text
    assert [button.label for button in page.button] == ["Xác minh thông tin"]
    assert [link.label for link in page.get("page_link")] == [
        "Tra cứu thông báo",
        "Xác minh  →",
        "Tra cứu  →",
        "Dành cho bạn  →",
        "Trang chủ",
        "Xác minh",
        "Tra cứu thông báo",
        "Dành cho bạn",
    ]


def test_verify_page_renders_translated_hierarchy_and_escapes_dynamic_text(monkeypatch):
    monkeypatch.setattr(
        api_client,
        "verify_claim",
        lambda *args, **kwargs: {
            "results": [
                {
                    "raw_claim_text": "Hạn chót <script>alert(1)</script>",
                    "verdict": "CONFLICT",
                    "temporal_status": "CURRENT",
                    "abstention_reason": None,
                    "field_results": {
                        "deadline": {
                            "state": "CONFLICT",
                            "claimed_text": "20/09/2026",
                            "official_text": "25/09/2026",
                        }
                    },
                    "primary_provenance": {
                        "title": "Thông báo <b>chính thức</b>",
                        "publication_date": "2026-09-01",
                        "exact_chunk_text": "Hạn chót là ngày 25/09/2026.",
                        "canonical_url": "https://dut.udn.vn/notice/1",
                    },
                }
            ]
        },
    )

    page = AppTest.from_file(ROOT / "frontend/pages/1_Verify.py").run()
    page.text_area[0].input("Nội dung cần kiểm tra").run()
    page.button[0].click().run()

    assert not page.exception and not page.error
    text = "\n".join(element.value for element in page.markdown)
    assert "Có thông tin mâu thuẫn" in text
    assert "Bạn nhận được" in text and "Nguồn chính thức" in text
    assert "&lt;script&gt;" in text and "<script>" not in text
    assert "&lt;b&gt;chính thức&lt;/b&gt;" in text
    assert "CONFLICT" not in text and "CURRENT" not in text
    assert page.get("link_button")[0].label == "Xem thông báo chính thức"


def test_verify_page_hides_retrieved_only_provenance_for_no_official_field(monkeypatch):
    notice_title = "THÔNG BÁO NỘP HỒ SƠ XÉT MIỄN, GIẢM HỌC PHÍ"
    monkeypatch.setattr(
        api_client,
        "verify_claim",
        lambda *args, **kwargs: {
            "results": [
                {
                    "raw_claim_text": "Sinh viên K26 đóng học phí 450.000 đồng trước 30/09/2026.",
                    "verdict": "INSUFFICIENT_EVIDENCE",
                    "temporal_status": "CURRENT",
                    "abstention_reason": "NO_OFFICIAL_FIELD",
                    "field_results": {},
                    "primary_provenance": {
                        "title": notice_title,
                        "publication_date": "2026-09-01",
                        "exact_chunk_text": "Nộp hồ sơ trước ngày 10/09/2026.",
                        "canonical_url": "https://dut.udn.vn/notice/24",
                    },
                }
            ]
        },
    )

    page = AppTest.from_file(ROOT / "frontend/pages/1_Verify.py").run()
    page.text_area[0].input("Nội dung cần kiểm tra").run()
    page.button[0].click().run()

    assert not page.exception and not page.error
    text = "\n".join(element.value for element in page.markdown)
    assert "Chưa đủ bằng chứng" in text
    assert "Chưa tìm thấy bằng chứng chính thức đủ phù hợp" in text
    assert "Có thông tin mâu thuẫn" not in text
    assert notice_title not in text
    assert "10/09/2026" not in text
    assert not page.get("link_button")


@pytest.mark.parametrize("verdict", ["VERIFIED", "PARTIALLY_VERIFIED", "CONFLICT"])
def test_verify_page_keeps_applicable_source_for_verdicts_with_evidence(monkeypatch, verdict):
    source_title = f"Nguồn phù hợp {verdict}"
    monkeypatch.setattr(
        api_client,
        "verify_claim",
        lambda *args, **kwargs: {
            "results": [
                {
                    "raw_claim_text": "Nội dung cần kiểm tra",
                    "verdict": verdict,
                    "temporal_status": "CURRENT",
                    "field_results": {},
                    "primary_provenance": {
                        "title": source_title,
                        "exact_chunk_text": "Bằng chứng chính thức có thể áp dụng.",
                        "canonical_url": "https://dut.udn.vn/notice/applicable",
                    },
                }
            ]
        },
    )

    page = AppTest.from_file(ROOT / "frontend/pages/1_Verify.py").run()
    page.text_area[0].input("Nội dung cần kiểm tra").run()
    page.button[0].click().run()

    assert not page.exception and not page.error
    text = "\n".join(element.value for element in page.markdown)
    assert "Nguồn chính thức" in text
    assert source_title in text
    assert page.get("link_button")[0].label == "Xem thông báo chính thức"


def test_verify_page_keeps_text_flow_and_declares_the_image_ocr_flow():
    source = (ROOT / "frontend/pages/1_Verify.py").read_text(encoding="utf-8")

    assert "st.text_area(" in source
    assert "st.file_uploader(" in source
    assert 'type=["png", "jpg", "jpeg", "webp"]' in source
    assert "api_client.verify_image(" in source
    assert "Nội dung hệ thống đọc được" in source
    assert source.count("render_verification_result(item)") == 2
