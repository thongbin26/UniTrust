from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.url_fetch.errors import URLFetchError
from app.url_fetch.models import URLExtractionResult
from app.url_fetch.validator import PublicURLValidator


MAX_DECODED_BODY_BYTES = 2 * 1024 * 1024
MAX_EXTRACTED_TEXT_CHARS = 24_000
MAX_REDIRECTS = 3
SUPPORTED_CONTENT_TYPES = {"text/html", "text/plain", "application/xhtml+xml"}
REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}
FETCH_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


class WebContentFetcher:
    """Fetch bounded public page text as user-supplied claim input."""

    def __init__(
        self,
        validator: PublicURLValidator | None = None,
        client_factory: Callable[[], Any] | None = None,
    ):
        self.validator = validator or PublicURLValidator()
        self.client_factory = client_factory or self._create_client

    @staticmethod
    def _create_client() -> httpx.Client:
        return httpx.Client(
            timeout=FETCH_TIMEOUT,
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": "UniTrust/1.0"},
        )

    @staticmethod
    def _content_type(response: httpx.Response) -> str:
        value = response.headers.get("content-type")
        if not value:
            raise URLFetchError("UNSUPPORTED_CONTENT_TYPE", "The link did not return supported text content.")
        media_type = value.split(";", 1)[0].strip().casefold()
        if media_type not in SUPPORTED_CONTENT_TYPES:
            raise URLFetchError("UNSUPPORTED_CONTENT_TYPE", "The link did not return supported text content.")
        return media_type

    @staticmethod
    def _read_bounded(response: httpx.Response) -> bytes:
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_DECODED_BODY_BYTES:
                    raise URLFetchError("TOO_LARGE", "The linked page is too large to process safely.")
            except ValueError:
                pass
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_bytes():
            total += len(chunk)
            if total > MAX_DECODED_BODY_BYTES:
                raise URLFetchError("TOO_LARGE", "The linked page is too large to process safely.")
            chunks.append(chunk)
        return b"".join(chunks)

    @staticmethod
    def _extract(content: bytes, content_type: str, encoding: str | None) -> tuple[str | None, str]:
        decoded = content.decode(encoding or "utf-8", errors="replace")
        if content_type == "text/plain":
            return None, _normalize_text(decoded)

        soup = BeautifulSoup(decoded, "html.parser")
        title = _normalize_text(soup.title.get_text(" ", strip=True)) if soup.title else None
        for node in soup(["script", "style", "noscript", "template"]):
            node.decompose()
        body = _normalize_text(soup.get_text(" ", strip=True))
        text = _normalize_text(" ".join(part for part in (title, body) if part))
        return title, text

    @staticmethod
    def _bounded_text(text: str) -> tuple[str, list[str]]:
        if len(text) <= MAX_EXTRACTED_TEXT_CHARS:
            return text, []
        return text[:MAX_EXTRACTED_TEXT_CHARS], ["CONTENT_TRUNCATED"]

    def fetch(self, url: str) -> URLExtractionResult:
        requested_url = url.strip() if isinstance(url, str) else url
        current = self.validator.validate(url).network_url
        redirects = 0

        try:
            with self.client_factory() as client:
                while True:
                    validated = self.validator.validate(current)
                    with client.stream("GET", validated.network_url) as response:
                        if response.status_code in REDIRECT_STATUS_CODES:
                            location = response.headers.get("location")
                            if not location:
                                raise URLFetchError("FETCH_FAILED", "The link redirected without a usable destination.")
                            if redirects >= MAX_REDIRECTS:
                                raise URLFetchError("TOO_MANY_REDIRECTS", "The link redirected too many times.")
                            current = urljoin(validated.network_url, location)
                            # Validate before the next request, including every redirect target.
                            self.validator.validate(current)
                            redirects += 1
                            continue

                        if not 200 <= response.status_code < 300:
                            raise URLFetchError("FETCH_FAILED", "The linked page could not be fetched.")
                        content_type = self._content_type(response)
                        content = self._read_bounded(response)
                        title, text = self._extract(content, content_type, response.encoding)
                    if not text:
                        raise URLFetchError("EMPTY_CONTENT", "The linked page did not contain readable text.")
                    text, warnings = self._bounded_text(text)
                    return URLExtractionResult(
                        requested_url=requested_url,
                        final_url=validated.network_url,
                        title=title,
                        text=text,
                        content_type=content_type,
                        warnings=warnings,
                    )
        except URLFetchError:
            raise
        except httpx.TimeoutException as exc:
            raise URLFetchError("FETCH_TIMEOUT", "The linked page took too long to respond.") from exc
        except httpx.HTTPError as exc:
            raise URLFetchError("FETCH_FAILED", "The linked page could not be fetched.") from exc
