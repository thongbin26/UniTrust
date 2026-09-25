import httpx
import pytest

from frontend.api_client import APIClient, URLVerificationRequestError


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"ok": True}


def test_text_verify_keeps_standard_timeout(monkeypatch):
    monkeypatch.setenv("API_STD_TIMEOUT", "11.0")
    monkeypatch.setenv("API_LLM_TIMEOUT", "90.0")
    monkeypatch.setenv("API_IMAGE_TIMEOUT", "120.0")
    captured = {}

    def post(url, *, json, timeout):
        captured.update(url=url, json=json, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", post)
    client = APIClient()

    assert client.verify_claim("Thông báo học phí", use_llm=False, top_k=5) == {"ok": True}
    assert captured["timeout"] == 11.0
    assert captured["json"] == {
        "text": "Thông báo học phí",
        "use_llm": False,
        "top_k": 5,
    }


def test_image_verify_uses_dedicated_timeout_and_preserves_multipart(monkeypatch):
    monkeypatch.setenv("API_STD_TIMEOUT", "10.0")
    monkeypatch.setenv("API_IMAGE_TIMEOUT", "120.0")
    captured = {}

    def post(url, *, files, data, timeout):
        captured.update(url=url, files=files, data=data, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", post)
    client = APIClient()

    assert client.verify_image(b"png", "notice.png", "image/png", top_k=7) == {"ok": True}
    assert captured == {
        "url": "http://127.0.0.1:8000/verify/image",
        "files": {"image": ("notice.png", b"png", "image/png")},
        "data": {"top_k": "7", "use_llm": "false"},
        "timeout": 120.0,
    }


def test_image_verify_with_llm_never_reduces_image_timeout(monkeypatch):
    monkeypatch.setenv("API_STD_TIMEOUT", "10.0")
    monkeypatch.setenv("API_LLM_TIMEOUT", "30.0")
    monkeypatch.setenv("API_IMAGE_TIMEOUT", "120.0")
    captured = {}

    def post(_url, *, files, data, timeout):
        captured.update(files=files, data=data, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", post)
    client = APIClient()

    client.verify_image(b"png", "notice.png", "image/png", use_llm=True)
    assert captured["timeout"] == 120.0
    assert captured["data"]["use_llm"] == "true"


def test_url_verify_uses_independent_bounded_timeout_and_json(monkeypatch):
    monkeypatch.setenv("API_STD_TIMEOUT", "10.0")
    monkeypatch.setenv("API_IMAGE_TIMEOUT", "120.0")
    monkeypatch.setenv("API_URL_TIMEOUT", "30.0")
    captured = {}

    def post(url, *, json, timeout):
        captured.update(url=url, json=json, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", post)
    client = APIClient()

    assert client.verify_url("https://example.org/post", top_k=7) == {"ok": True}
    assert captured == {
        "url": "http://127.0.0.1:8000/verify/url",
        "json": {"url": "https://example.org/post", "top_k": 7, "use_llm": False},
        "timeout": 30.0,
    }
    assert client.std_timeout == 10.0
    assert client.image_timeout == 120.0


def test_url_verify_with_llm_never_reduces_url_timeout(monkeypatch):
    monkeypatch.setenv("API_URL_TIMEOUT", "30.0")
    monkeypatch.setenv("API_LLM_TIMEOUT", "90.0")
    captured = {}

    def post(_url, *, json, timeout):
        captured.update(json=json, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", post)
    APIClient().verify_url("https://example.org", use_llm=True)
    assert captured["timeout"] == 90.0
    assert captured["json"]["use_llm"] is True


def test_url_verify_propagates_safe_api_error_code(monkeypatch):
    response = httpx.Response(
        422,
        json={"detail": {"code": "UNSAFE_URL", "message": "safe message"}},
        request=httpx.Request("POST", "http://127.0.0.1:8000/verify/url"),
    )
    monkeypatch.setattr(httpx, "post", lambda *_args, **_kwargs: response)

    with pytest.raises(URLVerificationRequestError) as raised:
        APIClient().verify_url("https://example.org")
    assert raised.value.code == "UNSAFE_URL"
