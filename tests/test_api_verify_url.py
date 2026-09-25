from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.deps import get_verification_service
from app.api.routes.verify_url import get_web_content_fetcher, router
from app.url_fetch.errors import URLFetchError
from app.url_fetch.models import URLExtractionResult
from app.verification.models import OverallVerdict, VerificationResult


EXTRACTED_TEXT = "Sinh viên K26 đóng học phí 450.000 đồng. Hạn cuối: 30/09/2026."


class FakeFetcher:
    def __init__(self, result=None, error=None):
        self.result = result or URLExtractionResult(
            requested_url="https://example.org/post",
            final_url="https://example.org/post",
            title="Thông báo học phí",
            text=EXTRACTED_TEXT,
            content_type="text/html",
        )
        self.error = error
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        if self.error:
            raise self.error
        return self.result


class RecordingVerificationService:
    def __init__(self):
        self.calls = []

    def verify(self, text, top_k=5):
        self.calls.append((text, top_k))
        return [VerificationResult(
            claim_id="url-claim",
            raw_claim_text=text,
            verdict=OverallVerdict.INSUFFICIENT_EVIDENCE,
        )]


def client(fetcher=None, service=None):
    app = FastAPI()
    app.include_router(router)
    fetcher = fetcher or FakeFetcher()
    service = service or RecordingVerificationService()
    app.dependency_overrides[get_web_content_fetcher] = lambda: fetcher
    app.dependency_overrides[get_verification_service] = lambda: service
    return TestClient(app), fetcher, service


def test_url_endpoint_returns_additive_metadata_and_delegates_exact_text():
    test_client, fetcher, service = client()

    response = test_client.post("/verify/url", json={
        "url": "https://example.org/post", "top_k": 7, "use_llm": True,
    })

    assert response.status_code == 200
    assert fetcher.calls == ["https://example.org/post"]
    assert service.calls == [(EXTRACTED_TEXT, 7)]
    payload = response.json()
    assert payload["input_type"] == "URL"
    assert payload["requested_url"] == "https://example.org/post"
    assert payload["final_url"] == "https://example.org/post"
    assert payload["page_title"] == "Thông báo học phí"
    assert payload["extracted_text"] == EXTRACTED_TEXT
    assert payload["content_type"] == "text/html"
    assert payload["warnings"] == []
    assert payload["original_input"] == EXTRACTED_TEXT


def test_url_metadata_preserves_redirect_unicode_and_warnings():
    result = URLExtractionResult(
        requested_url="https://official-looking.example/dut-notice",
        final_url="https://official-looking.example/final",
        title="Thông báo tiếng Việt",
        text=EXTRACTED_TEXT,
        content_type="text/plain",
        warnings=["CONTENT_TRUNCATED"],
    )
    test_client, _, service = client(FakeFetcher(result=result))

    response = test_client.post("/verify/url", json={"url": result.requested_url})

    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_url"] != payload["final_url"]
    assert payload["page_title"] == "Thông báo tiếng Việt"
    assert payload["warnings"] == ["CONTENT_TRUNCATED"]
    assert service.calls == [(EXTRACTED_TEXT, 5)]
    # A URL that merely looks official cannot create official provenance.
    assert payload["results"][0]["primary_provenance"] is None
    assert payload["results"][0]["verdict"] == "INSUFFICIENT_EVIDENCE"


@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("INVALID_URL", 422), ("UNSAFE_URL", 422), ("FETCH_TIMEOUT", 504),
        ("FETCH_FAILED", 502), ("TOO_LARGE", 413), ("UNSUPPORTED_CONTENT_TYPE", 415),
        ("EMPTY_CONTENT", 422), ("TOO_MANY_REDIRECTS", 422),
    ],
)
def test_url_fetch_errors_are_mapped_without_internal_details(code, status):
    test_client, _, service = client(FakeFetcher(error=URLFetchError(code, "safe public message")))

    response = test_client.post("/verify/url", json={"url": "https://example.org"})

    assert response.status_code == status
    assert response.json()["detail"] == {"code": code, "message": "safe public message"}
    assert not service.calls
    assert "127.0.0.1" not in response.text
    assert "Traceback" not in response.text


@pytest.mark.parametrize("payload", [
    {}, {"url": "https://example.org", "top_k": 0},
    {"url": "https://example.org", "top_k": 21}, {"url": "https://example.org", "extra": "forbidden"},
])
def test_url_request_validation_runs_before_fetch(payload):
    test_client, fetcher, service = client()

    response = test_client.post("/verify/url", json=payload)

    assert response.status_code == 422
    assert not fetcher.calls
    assert not service.calls


def test_main_openapi_exposes_verify_text_image_and_url_routes():
    from main import app

    paths = app.openapi()["paths"]
    assert "/verify" in paths
    assert "/verify/image" in paths
    assert "/verify/url" in paths
