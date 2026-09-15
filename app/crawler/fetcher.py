import time
from datetime import datetime, timezone

import httpx


RETRY_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_http_client() -> httpx.Client:
    return httpx.Client(
        timeout=15.0,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "UniTrust-V2-Research-Demo/0.1 "
                "(public university notice monitor)"
            )
        },
    )


def fetch_with_retry(
    client: httpx.Client,
    url: str,
    max_attempts: int = 3,
) -> tuple[httpx.Response, datetime]:

    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.get(url)

            if (
                response.status_code
                in RETRY_STATUS_CODES
            ):
                raise httpx.HTTPStatusError(
                    (
                        "Retryable HTTP "
                        f"{response.status_code}"
                    ),
                    request=response.request,
                    response=response,
                )

            response.raise_for_status()

            return response, utc_now()

        except (
            httpx.RequestError,
            httpx.HTTPStatusError,
        ) as exc:
            last_error = exc

            if attempt == max_attempts:
                break

            time.sleep(0.5 * attempt)

    assert last_error is not None

    raise last_error