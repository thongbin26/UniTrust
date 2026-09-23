from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from frontend.api_client import URLVerificationRequestError, api_client


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
        "Tra cứu thông báo chính thức",
        "Kiểm chứng  →",
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


@pytest.mark.parametrize(
    ("verdict", "received_action", "official_action", "expected_label"),
    [
        ("VERIFIED", "nộp", "submit", "Nộp"),
        ("CONFLICT", "đăng ký", "register", "Đăng ký"),
        ("VERIFIED", "ứng tuyển", "apply", "Ứng tuyển"),
        ("VERIFIED", "thanh toán", "pay", "Thanh toán"),
        ("VERIFIED", "tham gia", "attend", "Tham gia"),
        ("VERIFIED", "nhận", "collect", "Nhận"),
        ("VERIFIED", "kiểm tra", "check", "Kiểm tra"),
        ("VERIFIED", "cập nhật", "update", "Cập nhật"),
        ("VERIFIED", "thực hiện", "other", "Thực hiện"),
    ],
)
def test_verify_page_translates_canonical_action_values_for_students(
    monkeypatch, verdict, received_action, official_action, expected_label
):
    monkeypatch.setattr(
        api_client,
        "verify_claim",
        lambda *args, **kwargs: {
            "results": [
                {
                    "raw_claim_text": "Nội dung cần kiểm tra",
                    "verdict": verdict,
                    "temporal_status": "CURRENT",
                    "field_results": {
                        "action": {
                            "state": "MATCH",
                            "claimed_text": received_action,
                            "official_text": official_action,
                        }
                    },
                    "primary_provenance": {
                        "title": "Nguồn phù hợp",
                        "exact_chunk_text": "Bằng chứng chính thức có thể áp dụng.",
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
    assert received_action in text
    assert expected_label in text
    assert official_action not in text


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
    assert "api_client.verify_url(" in source
    assert "Kiểm chứng đường link" in source
    assert "Bạn nhận được thông tin từ đâu?" in source
    assert all(label in source for label in ("Văn bản", "Ảnh chụp", "Đường link"))
    assert "Nội dung hệ thống đọc được từ đường link" in source
    assert "Nội dung hệ thống đọc được" in source
    assert source.count("render_message_results(response)") == 3
    assert "Kết luận toàn bộ" in source
    assert "Nội dung {position}/{total}" in source


def _url_abstention_response():
    return {
        "requested_url": "https://official-looking.example/dut-notice",
        "final_url": "https://official-looking.example/final-notice",
        "page_title": "Thông báo học phí",
        "extracted_text": "Sinh viên K26 đóng học phí 450.000 đồng. Hạn cuối: 30/09/2026.",
        "warnings": ["CONTENT_TRUNCATED"],
        "results": [
            {
                "raw_claim_text": "Sinh viên K26 đóng học phí 450.000 đồng trước 30/09/2026.",
                "verdict": "INSUFFICIENT_EVIDENCE",
                "temporal_status": "CURRENT",
                "abstention_reason": "NO_OFFICIAL_FIELD",
                "field_results": {},
                "primary_provenance": {
                    "title": "THÔNG BÁO NỘP HỒ SƠ XÉT MIỄN, GIẢM HỌC PHÍ",
                    "exact_chunk_text": "Nộp hồ sơ trước ngày 10/09/2026.",
                    "canonical_url": "https://dut.udn.vn/notice/24",
                },
            }
        ],
    }


def test_verify_page_url_abstention_hides_retrieved_only_source_and_keeps_input_untrusted(monkeypatch):
    calls = []

    def verify_url(*args, **kwargs):
        calls.append((args, kwargs))
        return _url_abstention_response()

    monkeypatch.setattr(api_client, "verify_url", verify_url)
    page = AppTest.from_file(ROOT / "frontend/pages/1_Verify.py").run()
    page.radio[0].set_value("Đường link").run()
    page.text_input[0].input(" https://official-looking.example/dut-notice ").run()
    page.button[0].click().run()

    assert not page.exception and not page.error
    text = "\n".join(element.value for element in page.markdown)
    assert calls == [(("https://official-looking.example/dut-notice",), {"top_k": 5, "use_llm": False})]
    assert "Nội dung hệ thống đọc được từ đường link" in text
    assert "Thông báo học phí" in text
    assert "https://official-looking.example/dut-notice" in text
    assert "https://official-looking.example/final-notice" in text
    assert "chưa được xem là bằng chứng chính thức" in text
    assert "CONTENT_TRUNCATED" not in text
    assert [info.value for info in page.info] == [
        "Nội dung trang quá dài nên hệ thống chỉ sử dụng phần văn bản cần thiết trong giới hạn xử lý."
    ]
    assert "Chưa đủ bằng chứng" in text
    assert "Nguồn chính thức" not in text
    assert "THÔNG BÁO NỘP HỒ SƠ XÉT MIỄN" not in text
    assert "10/09/2026" not in text
    assert "Có thông tin mâu thuẫn" not in text
    assert page.text_area[0].value == _url_abstention_response()["extracted_text"]
    assert not page.get("link_button")


@pytest.mark.parametrize("verdict", ["VERIFIED", "PARTIALLY_VERIFIED", "CONFLICT"])
def test_verify_page_url_keeps_applicable_official_source(monkeypatch, verdict):
    source_title = f"Nguồn URL phù hợp {verdict}"
    monkeypatch.setattr(
        api_client,
        "verify_url",
        lambda *_args, **_kwargs: {
            "requested_url": "https://example.org/received",
            "final_url": "https://example.org/received",
            "page_title": "Nội dung nhận được",
            "extracted_text": "Sinh viên cần đóng học phí.",
            "warnings": [],
            "results": [
                {
                    "raw_claim_text": "Sinh viên cần đóng học phí.",
                    "verdict": verdict,
                    "temporal_status": "CURRENT",
                    "field_results": {},
                    "primary_provenance": {
                        "title": source_title,
                        "exact_chunk_text": "Thông báo chính thức có thể áp dụng.",
                        "canonical_url": "https://dut.udn.vn/notice/applicable",
                    },
                }
            ],
        },
    )

    page = AppTest.from_file(ROOT / "frontend/pages/1_Verify.py").run()
    page.radio[0].set_value("Đường link").run()
    page.text_input[0].input("https://example.org/received").run()
    page.button[0].click().run()

    assert not page.exception and not page.error
    text = "\n".join(element.value for element in page.markdown)
    assert "chưa được xem là bằng chứng chính thức" in text
    assert "Nguồn chính thức" in text
    assert source_title in text
    assert page.get("link_button")[0].label == "Xem thông báo chính thức"


def test_verify_page_url_empty_input_does_not_call_api(monkeypatch):
    calls = []
    monkeypatch.setattr(api_client, "verify_url", lambda *_args, **_kwargs: calls.append(True))
    page = AppTest.from_file(ROOT / "frontend/pages/1_Verify.py").run()
    page.radio[0].set_value("Đường link").run()
    page.text_input[0].input("   ").run()
    page.button[0].click().run()

    assert not page.exception
    assert calls == []
    assert [warning.value for warning in page.warning] == ["Vui lòng nhập đường link cần kiểm chứng."]


@pytest.mark.parametrize(("activity", "label"), [("NEW", "Mới"), ("UPDATED", "Vừa cập nhật")])
def test_evidence_page_shows_monitor_badge_only_for_persisted_activity(monkeypatch, activity, label):
    import streamlit as st
    st.cache_data.clear()
    monkeypatch.setattr(api_client, "get_search_index", lambda: [{
        "notice_id": 999, "title": "Thông báo thử nghiệm", "source_id": "dut_academic",
        "source_display_name": "Nguồn DUT", "searchable_text": "Nội dung", "monitoring_activity": activity,
    }])
    page = AppTest.from_file(ROOT / "frontend/pages/2_Evidence.py").run()
    assert not page.exception and not page.error
    text = "\n".join(element.value for element in page.markdown)
    assert label in text


def test_for_you_page_imports_with_monitoring_datetime_formatter():
    page = AppTest.from_file(ROOT / "frontend/pages/3_For_You.py").run()
    assert not page.exception and not page.error


def test_verify_page_url_renders_safe_fetch_error(monkeypatch):
    monkeypatch.setattr(
        api_client,
        "verify_url",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(URLVerificationRequestError("UNSAFE_URL")),
    )
    page = AppTest.from_file(ROOT / "frontend/pages/1_Verify.py").run()
    page.radio[0].set_value("Đường link").run()
    page.text_input[0].input("https://127.0.0.1/private").run()
    page.button[0].click().run()

    assert not page.exception
    assert [error.value for error in page.error] == [
        "Đường link này không thể được truy cập vì lý do an toàn."
    ]
