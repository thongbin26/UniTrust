from pathlib import Path

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
    assert len(page.get("page_link")) == 1


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
    assert "Bạn nhận được:" in text and "Nguồn chính thức:" in text
    assert "&lt;script&gt;" in text and "<script>" not in text
    assert "&lt;b&gt;chính thức&lt;/b&gt;" in text
    assert "CONFLICT" not in text and "CURRENT" not in text
    assert page.get("link_button")[0].label == "Xem thông báo chính thức"
