import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

from app.crawler.dut_parser import (
    extract_notice_links,
    parse_notice_detail,
)
from app.crawler.fetcher import (
    create_http_client,
    fetch_with_retry,
)
from app.crawler.repository import (
    init_notice_tables,
    record_crawl_failure,
    save_notice,
)
from app.db.database import init_database
from app.sources.repository import (
    get_source,
    seed_sources,
)


RAW_DATA_DIR = Path(
    "data/raw"
)


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def save_raw_html(
    source_id: str,
    content: bytes,
) -> tuple[str, str]:

    raw_hash = hashlib.sha256(
        content
    ).hexdigest()

    source_dir = (
        RAW_DATA_DIR
        / source_id
    )

    source_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        source_dir
        / f"{raw_hash}.html"
    )

    if not path.exists():
        path.write_bytes(content)

    return (
        raw_hash,
        str(path),
    )


def crawl_source(
    source_id: str,
    limit: int = 10,
    delay_seconds: float = 0.4,
) -> dict:

    init_database()
    seed_sources()
    init_notice_tables()

    source = get_source(
        source_id
    )

    if source is None:
        raise ValueError(
            f"Unknown source: {source_id}"
        )

    stats = {
        "source_id": source_id,
        "discovered": 0,
        "created": 0,
        "updated": 0,
        "unchanged": 0,
        "failed": 0,
    }

    with create_http_client() as client:

        try:
            listing_response, _ = (
                fetch_with_retry(
                    client,
                    source.listing_url,
                )
            )

        except Exception as exc:
            record_crawl_failure(
                source_id=source_id,
                url=source.listing_url,
                stage="listing",
                error=exc,
            )

            raise

        links = extract_notice_links(
            html=listing_response.text,
            listing_url=(
                str(
                    listing_response.url
                )
            ),
            official_domain=(
                source.official_domain
            ),
            limit=limit,
        )

        stats["discovered"] = len(
            links
        )

        for link in links:

            observed_at = utc_now()

            try:
                response, fetched_at = (
                    fetch_with_retry(
                        client,
                        link.url,
                    )
                )

                raw_hash, raw_path = (
                    save_raw_html(
                        source_id,
                        response.content,
                    )
                )

                notice = (
                    parse_notice_detail(
                        html=response.text,
                        source_id=source_id,
                        final_url=str(
                            response.url
                        ),
                        observed_at=(
                            observed_at
                        ),
                        fetched_at=(
                            fetched_at
                        ),
                        raw_html_hash=(
                            raw_hash
                        ),
                        raw_html_path=(
                            raw_path
                        ),
                    )
                )

                status = save_notice(
                    notice
                )

                stats[
                    status.lower()
                ] += 1

            except Exception as exc:
                stats["failed"] += 1

                record_crawl_failure(
                    source_id=source_id,
                    url=link.url,
                    stage="detail",
                    error=exc,
                )

            time.sleep(
                delay_seconds
            )

    return stats