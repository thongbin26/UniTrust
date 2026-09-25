from __future__ import annotations

import socket

import httpx
import pytest

from app.url_fetch.errors import URLFetchError
from app.url_fetch.fetcher import (
    MAX_DECODED_BODY_BYTES,
    MAX_EXTRACTED_TEXT_CHARS,
    WebContentFetcher,
)
from app.url_fetch.validator import PublicURLValidator


PUBLIC_V4 = "8.8.8.8"
PUBLIC_V6 = "2606:4700:4700::1111"


def resolver_for(mapping):
    def resolve(host, _port):
        value = mapping.get(host, [PUBLIC_V4])
        if isinstance(value, Exception):
            raise value
        return [(socket.AF_INET6 if ":" in address else socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443)) for address in value]
    return resolve


def fetcher(handler, mapping=None):
    return WebContentFetcher(
        validator=PublicURLValidator(resolver_for(mapping or {})),
        client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False, trust_env=False),
    )


def assert_error(code, callback):
    with pytest.raises(URLFetchError) as raised:
        callback()
    assert raised.value.code == code


@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "ftp://example.org/file", "data:text/plain,hello", "example.org", "http:///missing",
])
def test_invalid_schemes_and_incomplete_urls_are_rejected(url):
    assert_error("INVALID_URL", lambda: PublicURLValidator(resolver_for({})).validate(url))


@pytest.mark.parametrize("url", [
    "https://user:password@example.org", "http://localhost", "http://localhost.localdomain",
    "http://api.localhost", "http://router", "http://intranet", "http://example.org:bad",
])
def test_credentials_and_internal_hostnames_are_rejected(url):
    assert_error("UNSAFE_URL" if "bad" not in url else "INVALID_URL", lambda: PublicURLValidator(resolver_for({})).validate(url))


@pytest.mark.parametrize("url", [
    "http://127.0.0.1", "http://[::1]", "http://0.0.0.0", "http://169.254.169.254",
    "http://10.0.0.1", "http://172.16.0.1", "http://192.168.1.1", "http://[fc00::1]", "http://[fe80::1]",
])
def test_non_global_literal_addresses_are_blocked(url):
    assert_error("UNSAFE_URL", lambda: PublicURLValidator(resolver_for({})).validate(url))


def test_public_hostname_and_ipv6_are_accepted_by_injectable_resolution():
    validator = PublicURLValidator(resolver_for({"example.org": [PUBLIC_V4], "example.net": [PUBLIC_V6]}))
    assert validator.validate("HTTPS://example.org/path#fragment").network_url == "https://example.org/path"
    assert validator.validate("http://example.net/").hostname == "example.net"


def test_mixed_or_empty_or_failed_resolution_is_safe_failure():
    assert_error("UNSAFE_URL", lambda: PublicURLValidator(resolver_for({"example.org": [PUBLIC_V4, "127.0.0.1"]})).validate("https://example.org"))
    assert_error("FETCH_FAILED", lambda: PublicURLValidator(resolver_for({"example.org": []})).validate("https://example.org"))
    assert_error("FETCH_FAILED", lambda: PublicURLValidator(resolver_for({"example.org": socket.gaierror()})).validate("https://example.org"))


def test_html_extraction_removes_non_visible_content_and_preserves_vietnamese():
    html = "<html><head><title>Thông báo học phí</title><style>secret-style</style></head><body><script>secret-script</script><noscript>secret-noscript</noscript><template>secret-template</template><main>Sinh viên đóng học phí 450.000 đồng.</main></body></html>"
    result = fetcher(lambda request: httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=html.encode())).fetch("https://example.org")
    assert result.title == "Thông báo học phí"
    assert "Sinh viên đóng học phí 450.000 đồng." in result.text
    assert "secret-" not in result.text


@pytest.mark.parametrize("content_type", ["text/plain; charset=UTF-8", "application/xhtml+xml"])
def test_supported_text_content_types(content_type):
    result = fetcher(lambda request: httpx.Response(200, headers={"content-type": content_type}, content="Tiếng Việt\n  rõ ràng".encode())).fetch("https://example.org")
    assert "Tiếng Việt rõ ràng" in result.text


@pytest.mark.parametrize("headers, content, code", [
    ({}, b"x", "UNSUPPORTED_CONTENT_TYPE"),
    ({"content-type": "application/pdf"}, b"x", "UNSUPPORTED_CONTENT_TYPE"),
    ({"content-type": "text/plain"}, b"", "EMPTY_CONTENT"),
    ({"content-type": "text/plain", "content-length": str(MAX_DECODED_BODY_BYTES + 1)}, b"x", "TOO_LARGE"),
])
def test_content_failures_are_safe(headers, content, code):
    assert_error(code, lambda: fetcher(lambda request: httpx.Response(200, headers=headers, content=content)).fetch("https://example.org"))


def test_streamed_decoded_body_limit_and_extracted_text_limit_are_enforced():
    body = b"x" * (MAX_DECODED_BODY_BYTES + 1)
    assert_error("TOO_LARGE", lambda: fetcher(lambda request: httpx.Response(200, headers={"content-type": "text/plain"}, content=body)).fetch("https://example.org"))
    text = "x" * (MAX_EXTRACTED_TEXT_CHARS + 10)
    result = fetcher(lambda request: httpx.Response(200, headers={"content-type": "text/plain"}, content=text.encode())).fetch("https://example.org")
    assert len(result.text) == MAX_EXTRACTED_TEXT_CHARS
    assert result.warnings == ["CONTENT_TRUNCATED"]


def test_timeouts_transport_failures_and_http_errors_are_safe():
    assert_error("FETCH_TIMEOUT", lambda: fetcher(lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("slow"))).fetch("https://example.org"))
    assert_error("FETCH_FAILED", lambda: fetcher(lambda request: (_ for _ in ()).throw(httpx.ConnectError("offline"))).fetch("https://example.org"))
    assert_error("FETCH_FAILED", lambda: fetcher(lambda request: httpx.Response(404, headers={"content-type": "text/plain"})).fetch("https://example.org"))


def test_public_redirects_are_revalidated_and_relative_redirects_work():
    requests = []
    def handler(request):
        requests.append(str(request.url))
        if request.url.path == "/start":
            return httpx.Response(302, headers={"location": "/finish"})
        return httpx.Response(200, headers={"content-type": "text/plain"}, content=b"done")
    result = fetcher(handler).fetch("https://example.org/start")
    assert result.final_url == "https://example.org/finish"
    assert requests == ["https://example.org/start", "https://example.org/finish"]


def test_public_redirect_to_localhost_is_blocked_before_target_request():
    requests = []
    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://127.0.0.1:8000/private"})
    assert_error("UNSAFE_URL", lambda: fetcher(handler).fetch("https://example.org/start"))
    assert requests == ["https://example.org/start"]


def test_public_redirect_to_mixed_address_host_is_blocked_before_target_request():
    requests = []
    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://mixed.example/"})
    assert_error("UNSAFE_URL", lambda: fetcher(handler, {"mixed.example": [PUBLIC_V4, "10.0.0.1"]}).fetch("https://example.org/start"))
    assert requests == ["https://example.org/start"]


def test_redirect_limit_and_loop_are_bounded():
    def handler(request):
        return httpx.Response(302, headers={"location": f"https://example.org{request.url.path}next"})
    assert_error("TOO_MANY_REDIRECTS", lambda: fetcher(handler).fetch("https://example.org/"))
