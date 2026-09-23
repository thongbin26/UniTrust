from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.api.schemas import NoticeSearchIndexItem
from frontend.api_client import api_client
from tests.phase1_fixtures import phase1_client, frontend_http


def test_evidence_api_list(phase1_client):
    response = phase1_client.get("/evidence/notices")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all(item["has_structured_obligations"] for item in response.json())


def test_evidence_api_not_found(phase1_client):
    assert phase1_client.get("/evidence/notices/999999").status_code == 404


def test_evidence_api_changes(phase1_client):
    response = phase1_client.get("/evidence/notices/13/changes")
    assert response.status_code == 200
    assert response.json() == {"has_history": False, "changes": []}


def test_search_index_client_and_contract(phase1_client, frontend_http):
    items = api_client.get_search_index()
    assert frontend_http == [("GET", "/evidence/search-index", None, api_client.std_timeout)]
    assert items == phase1_client.get("/evidence/search-index").json()
    assert len(items) == 2
    for item in items:
        assert set(item) == set(NoticeSearchIndexItem.model_fields)
        assert set(item) == {"notice_id", "title", "source_id", "source_display_name", "searchable_text", "monitoring_activity"}
        NoticeSearchIndexItem.model_validate(item)
        detail = phase1_client.get(f"/evidence/notices/{item['notice_id']}").json()
        assert item["searchable_text"] == detail["raw_text"]
        assert item["source_display_name"] == detail["source_name"]


def test_evidence_page_browses_searches_then_fetches_selected_detail(frontend_http, monkeypatch):
    selection = [None]
    searchbox = {}

    def select(search_function, **kwargs):
        searchbox.update(kwargs, search=search_function)
        return selection[0]

    monkeypatch.setattr("streamlit_searchbox.st_searchbox", select)
    page = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/pages/2_Evidence.py").run(timeout=20)
    assert not page.exception and not page.error
    assert len(searchbox["default_options"]) == 2
    assert searchbox["search"]("tốt nghiệp")
    assert [call[1] for call in frontend_http] == ["/evidence/search-index"]

    selection[0] = 13
    page.run()
    assert not page.exception and not page.error
    assert [call[1] for call in frontend_http] == [
        "/evidence/search-index", "/evidence/notices/13", "/evidence/notices/13/changes", "/evidence/notices/13/versions",
    ]
    # Index has no coverage fields; exercise real page rendering without them.
    assert any("THÔNG BÁO THỜI GIAN" in element.value for element in page.markdown)


def test_evidence_page_empty_index(frontend_http, monkeypatch):
    monkeypatch.setattr(api_client, "get_search_index", lambda: [])
    page = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/pages/2_Evidence.py").run()
    assert not page.exception and not page.error
    assert any("Chưa có thông báo để tra cứu" in element.value for element in page.markdown)
    assert frontend_http == []


def test_evidence_page_hides_request_errors(frontend_http, monkeypatch):
    def fail():
        raise RuntimeError("private backend URL / Python exception details")

    monkeypatch.setattr(api_client, "get_search_index", fail)
    page = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/pages/2_Evidence.py").run()
    assert not page.exception
    assert [error.value for error in page.error] == ["Không thể tải thông báo lúc này. Vui lòng thử lại."]
