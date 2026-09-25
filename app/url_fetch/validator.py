from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Callable, Iterable
from urllib.parse import SplitResult, urlsplit, urlunsplit

from app.url_fetch.errors import URLFetchError


Resolver = Callable[[str, int], Iterable[object]]


@dataclass(frozen=True)
class ValidatedURL:
    requested_url: str
    network_url: str
    hostname: str
    port: int


def default_resolver(hostname: str, port: int) -> list[tuple]:
    return socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)


def _safe_error(code: str, message: str) -> URLFetchError:
    return URLFetchError(code, message)


def _is_literal_ip(hostname: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(hostname)
    except ValueError:
        return None


def _require_global(address: str) -> None:
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError as exc:
        raise _safe_error("FETCH_FAILED", "The URL host could not be resolved safely.") from exc
    if not parsed.is_global:
        raise _safe_error("UNSAFE_URL", "The URL must point to a public internet address.")


def _address_from_resolution(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, tuple) and len(value) >= 5:
        sockaddr = value[4]
        if isinstance(sockaddr, tuple) and sockaddr:
            return str(sockaddr[0])
    raise _safe_error("FETCH_FAILED", "The URL host could not be resolved safely.")


class PublicURLValidator:
    """Validate public destinations before each HTTP request.

    This pre-resolution policy reduces SSRF risk for the local demo but does not
    pin the later TCP connection against every possible DNS-rebinding race.
    """

    def __init__(self, resolver: Resolver | None = None):
        self.resolver = resolver or default_resolver

    def validate(self, url: str) -> ValidatedURL:
        if not isinstance(url, str) or not url.strip():
            raise _safe_error("INVALID_URL", "Enter a complete public HTTP(S) URL.")

        requested_url = url.strip()
        try:
            parsed = urlsplit(requested_url)
            port = parsed.port
        except ValueError as exc:
            raise _safe_error("INVALID_URL", "The URL contains an invalid port.") from exc

        scheme = parsed.scheme.casefold()
        hostname = parsed.hostname
        if scheme not in {"http", "https"}:
            raise _safe_error("INVALID_URL", "Only HTTP and HTTPS links are supported.")
        if not hostname:
            raise _safe_error("INVALID_URL", "Enter a complete public HTTP(S) URL.")
        if parsed.username is not None or parsed.password is not None:
            raise _safe_error("UNSAFE_URL", "Links containing credentials are not supported.")

        hostname = hostname.casefold().rstrip(".")
        if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".localhost"):
            raise _safe_error("UNSAFE_URL", "The URL must point to a public internet address.")

        literal = _is_literal_ip(hostname)
        if literal is not None:
            _require_global(str(literal))
        else:
            if "." not in hostname:
                raise _safe_error("UNSAFE_URL", "The URL must point to a public internet address.")
            try:
                resolved = list(self.resolver(hostname, port or (443 if scheme == "https" else 80)))
            except URLFetchError:
                raise
            except OSError as exc:
                raise _safe_error("FETCH_FAILED", "The URL host could not be resolved safely.") from exc
            if not resolved:
                raise _safe_error("FETCH_FAILED", "The URL host could not be resolved safely.")
            for item in resolved:
                _require_global(_address_from_resolution(item))

        network_url = urlunsplit(SplitResult(
            scheme=scheme,
            netloc=parsed.netloc,
            path=parsed.path or "/",
            query=parsed.query,
            fragment="",
        ))
        return ValidatedURL(requested_url, network_url, hostname, port or (443 if scheme == "https" else 80))
