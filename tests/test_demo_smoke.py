import json

import httpx
import pytest

from scripts import smoke_test as smoke


def handler(request):
    path = request.url.path
    if path == "/health":
        return httpx.Response(200, json={"status": "ok", "database": "ok", "service": "UniTrust"})
    if path == "/_stcore/health":
        return httpx.Response(200, text="ok")
    if path == "/evidence/search-index":
        return httpx.Response(200, json=[{
            "notice_id": 99, "title": "Fixture title", "source_id": "fixture",
            "source_display_name": "Fixture source", "searchable_text": "Fixture content",
        }])
    if path == "/for-you":
        assert json.loads(request.content) == {"major": "CNTT", "cohort": "K22"}
        return httpx.Response(200, json={"obligations": [{
            "action_text": "Submit form", "applicability": {"status": "UNKNOWN", "explanation": "missing program"},
        }]})
    if path == "/verify":
        assert json.loads(request.content)["use_llm"] is False
        return httpx.Response(200, json={"results": [{
            "verdict": "INSUFFICIENT_EVIDENCE", "field_results": {},
        }]})
    raise AssertionError(f"Unexpected request: {request.url}")


def test_smoke_uses_current_contracts_without_fixed_notice_or_verdict():
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        smoke.run_checks(client)


@pytest.mark.parametrize("path,response", [
    ("/health", httpx.Response(200, json={"status": "degraded"})),
    ("/evidence/search-index", httpx.Response(200, json={"status": "ok"})),
    ("/for-you", httpx.Response(200, json={"obligations": [{"obligation": "wrong shape"}]})),
    ("/verify", httpx.Response(200, json={"results": []})),
])
def test_smoke_rejects_failed_or_wrong_shape_responses(path, response):
    with httpx.Client(transport=httpx.MockTransport(
        lambda request: response if request.url.path == path else handler(request)
    )) as client:
        with pytest.raises(smoke.SmokeFailure):
            smoke.run_checks(client)


def test_smoke_main_returns_failure_on_http_error(monkeypatch):
    original_client = httpx.Client
    monkeypatch.setattr(smoke.httpx, "Client", lambda **kwargs: original_client(
        transport=httpx.MockTransport(lambda request: httpx.Response(503)),
    ))
    assert smoke.main() == 1
