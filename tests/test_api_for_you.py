from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.api.schemas import ForYouResponse
from frontend.api_client import api_client
from frontend.profile_state import api_profile, load_catalog, make_profile
from tests.phase1_fixtures import phase1_client, frontend_http


def cntt_profile():
    return make_profile(load_catalog(), "Khoa Công nghệ Thông tin", "Công nghệ thông tin", "K22")


def test_api_client_for_you_uses_real_contract(phase1_client, frontend_http):
    profile = api_profile(cntt_profile())
    response = api_client.for_you(profile)
    assert frontend_http == [("POST", "/for-you", profile, api_client.std_timeout)]
    assert response == phase1_client.post("/for-you", json=profile).json()
    assert set(response) == {"obligations"}
    assert len(response["obligations"]) == 6
    ForYouResponse.model_validate(response)
    obligation = next(o for o in response["obligations"] if o["notice_id"] == 13 and o["obligation_id"] == "o2")
    assert obligation["action_text"]
    assert obligation["applicability"]["status"] == "APPLIES"
    assert "obligation" not in obligation and "applicability_status" not in obligation
    assert obligation["temporal_status"] == "CURRENT"


def test_existing_exact_match_and_missing_dimension_semantics(phase1_client):
    def result(major, cohort):
        items = phase1_client.post("/for-you", json={"major": major, "cohort": cohort}).json()["obligations"]
        return next(o for o in items if o["notice_id"] == 13 and o["obligation_id"] == "o2")

    assert result("CNTT", "K22")["applicability"]["status"] == "APPLIES"
    assert result("Công nghệ thông tin", "K22")["applicability"]["status"] == "DOES_NOT_APPLY"
    assert result("CNTT", None)["applicability"]["status"] == "DOES_NOT_APPLY"
    items = phase1_client.post("/for-you", json={"program": None}).json()["obligations"]
    program_item = next(o for o in items if o["notice_id"] == 24 and o["obligation_id"] == "o1")
    assert program_item["applicability"]["status"] == "DOES_NOT_APPLY"


def test_for_you_page_renders_real_response(frontend_http, phase1_client):
    page = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/pages/3_For_You.py")
    page.session_state["student_profile"] = cntt_profile()
    page.session_state["edit_mode"] = False
    page.run(timeout=20)
    assert not page.exception and not page.error
    assert frontend_http[0][2]["major"] == "CNTT"
    assert frontend_http[0][2]["program"] is None
    items = phase1_client.post("/for-you", json=api_profile(cntt_profile())).json()["obligations"]
    text = "\n".join(element.value for element in page.markdown)
    assert all(item["action_text"] in text for item in items)
    assert "Công nghệ thông tin" in text
    assert "Việc áp dụng cho bạn (1)" in text
    assert "Cần kiểm tra thêm" in text


def test_for_you_page_hides_request_errors(frontend_http, monkeypatch):
    def fail(profile):
        raise RuntimeError("private backend URL / Python exception details")

    monkeypatch.setattr(api_client, "for_you", fail)
    page = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/pages/3_For_You.py")
    page.session_state["student_profile"] = cntt_profile()
    page.run()
    assert not page.exception
    assert [error.value for error in page.error] == ["Không thể tải thông tin dành cho bạn lúc này. Vui lòng thử lại."]
