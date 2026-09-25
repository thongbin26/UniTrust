import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from app.models.source import (
    SourceCheckResult,
    SourceHealthStatus,
    SourceRead,
)
from app.sources.repository import (
    list_sources,
    save_health_result,
)


DEFAULT_TIMEOUT = 10.0


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hostname_is_official(
    url: str,
    official_domain: str,
) -> bool:

    hostname = urlparse(url).hostname

    if hostname is None:
        return False

    hostname = hostname.lower()
    official_domain = official_domain.lower()

    return (
        hostname == official_domain
        or hostname.endswith("." + official_domain)
    )


def check_source(
    source: SourceRead,
    client: httpx.Client | None = None,
) -> SourceCheckResult:

    checked_at = utc_now()

    owns_client = client is None

    if client is None:
        client = httpx.Client(
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "UniTrust-V2-Research-Demo/0.1 "
                    "(university notice monitor)"
                )
            },
        )

    try:
        response = client.get(source.listing_url)

        body = response.content

        content_hash = hashlib.sha256(body).hexdigest()

        final_url = str(response.url)

        status = SourceHealthStatus.HEALTHY
        error = None

        if response.status_code in {403, 429}:
            status = SourceHealthStatus.DEGRADED
            error = (
                f"Source reachable but access is limited: "
                f"HTTP {response.status_code}"
            )

        elif response.status_code >= 400:
            status = SourceHealthStatus.FAILED
            error = f"HTTP {response.status_code}"

        elif not hostname_is_official(
            final_url,
            source.official_domain,
        ):
            status = SourceHealthStatus.DEGRADED
            error = (
                "Final URL is outside the configured "
                "official domain."
            )

        elif len(body) < 500:
            status = SourceHealthStatus.DEGRADED
            error = "Response body is unexpectedly small."

        elif (
            source.expected_marker
            and source.expected_marker.casefold()
            not in response.text.casefold()
        ):
            status = SourceHealthStatus.DEGRADED
            error = (
                "Expected page marker was not found. "
                "The page layout may have changed."
            )

        result = SourceCheckResult(
            source_id=source.source_id,
            name=source.name,
            health_status=status,
            checked_at=checked_at,
            http_status=response.status_code,
            final_url=final_url,
            content_hash=content_hash,
            content_length=len(body),
            error=error,
        )

    except httpx.RequestError as exc:

        result = SourceCheckResult(
            source_id=source.source_id,
            name=source.name,
            health_status=SourceHealthStatus.FAILED,
            checked_at=checked_at,
            error=str(exc),
        )

    finally:
        if owns_client:
            client.close()

    save_health_result(result)

    return result


def check_all_sources() -> list[SourceCheckResult]:

    sources = [source for source in list_sources() if source.enabled]

    return [
        check_source(source)
        for source in sources
    ]
