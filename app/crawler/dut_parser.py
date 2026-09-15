import hashlib
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup, NavigableString

from app.models.notice import (
    CrawledNotice,
    NoticeLink,
)


DATE_RE = re.compile(
    r"\b\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}\b"
)

NOTICE_ID_RE = re.compile(
    r"/Thongbao/id/(\d+)",
    re.IGNORECASE,
)

STOP_MARKERS = (
    "CÁC THÔNG TIN KHÁC",
    "TUYỂN SINH & ĐÀO TẠO",
    "CÁC LIÊN KẾT KHÁC",
)

ATTACHMENT_EXTENSIONS = (
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
)


def clean_text(value: str) -> str:
    return " ".join(value.split())


def official_hostname(
    url: str,
    official_domain: str,
) -> bool:
    hostname = urlparse(url).hostname

    if not hostname:
        return False

    hostname = hostname.lower()
    official_domain = official_domain.lower()

    return (
        hostname == official_domain
        or hostname.endswith(
            "." + official_domain
        )
    )


def extract_notice_links(
    html: str,
    listing_url: str,
    official_domain: str,
    limit: int | None = None,
) -> list[NoticeLink]:

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    results: list[NoticeLink] = []
    seen: set[str] = set()

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        absolute_url = urljoin(
            listing_url,
            anchor["href"],
        )

        if not official_hostname(
            absolute_url,
            official_domain,
        ):
            continue

        match = NOTICE_ID_RE.search(
            urlparse(absolute_url).path
        )

        if not match:
            continue

        if absolute_url in seen:
            continue

        seen.add(absolute_url)

        results.append(
            NoticeLink(
                url=absolute_url,
                external_id=match.group(1),
            )
        )

        if (
            limit is not None
            and len(results) >= limit
        ):
            break

    return results


def parse_dut_datetime(
    value: str,
) -> datetime | None:

    match = DATE_RE.search(value)

    if not match:
        return None

    parsed = datetime.strptime(
        match.group(0),
        "%d/%m/%Y %H:%M",
    )

    return parsed.replace(
        tzinfo=ZoneInfo(
            "Asia/Ho_Chi_Minh"
        )
    )


def find_primary_date_node(
    soup: BeautifulSoup,
):
    return soup.find(
        string=lambda text: (
            bool(
                text
                and DATE_RE.search(text)
            )
        )
    )


def extract_title(
    soup: BeautifulSoup,
    date_node,
) -> str:

    if date_node is not None:
        heading = date_node.find_previous(
            ["h1", "h2", "h3"]
        )

        if heading:
            title = clean_text(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )

            if title:
                return title

    if soup.title:
        return clean_text(
            soup.title.get_text(
                " ",
                strip=True,
            )
        )

    return "Untitled notice"


def extract_article_text(
    date_node,
    title: str,
) -> tuple[str, str]:

    if date_node is None:
        return title, "title_only"

    pieces: list[str] = []

    for element in date_node.parent.next_elements:

        if not isinstance(
            element,
            NavigableString,
        ):
            continue

        parent_name = (
            element.parent.name
            if element.parent
            else None
        )

        if parent_name in {
            "script",
            "style",
            "noscript",
        }:
            continue

        text = clean_text(
            str(element)
        )

        if not text:
            continue

        upper_text = text.upper()

        if any(
            marker in upper_text
            for marker in STOP_MARKERS
        ):
            break

        if text == title:
            continue

        if DATE_RE.fullmatch(text):
            continue

        if (
            pieces
            and pieces[-1] == text
        ):
            continue

        pieces.append(text)

    article_text = "\n".join(pieces).strip()

    if len(article_text) < 20:
        return title, "title_only"

    return article_text, "body"


def looks_like_attachment(
    url: str,
) -> bool:

    parsed = urlparse(url)

    hostname = (
        parsed.hostname or ""
    ).lower()

    path = parsed.path.lower()

    if hostname in {
        "drive.google.com",
        "docs.google.com",
    }:
        return True

    return path.endswith(
        ATTACHMENT_EXTENSIONS
    )


def extract_attachments(
    soup: BeautifulSoup,
    page_url: str,
) -> list[str]:

    attachments: list[str] = []
    seen: set[str] = set()

    for element in soup.find_all(
        ["a", "iframe", "embed", "object"]
    ):
        raw_url = (
            element.get("href")
            or element.get("src")
            or element.get("data")
        )

        if not raw_url:
            continue

        absolute_url = urljoin(
            page_url,
            raw_url,
        )

        if not looks_like_attachment(
            absolute_url
        ):
            continue

        if absolute_url in seen:
            continue

        seen.add(absolute_url)
        attachments.append(
            absolute_url
        )

    return attachments


def build_content_hash(
    title: str,
    publication_date: datetime | None,
    raw_text: str,
    attachment_links: list[str],
) -> str:

    normalized = {
        "title": clean_text(title),
        "publication_date": (
            publication_date.isoformat()
            if publication_date
            else None
        ),
        "raw_text": clean_text(
            raw_text
        ),
        "attachments": sorted(
            attachment_links
        ),
    }

    payload = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


def parse_notice_detail(
    html: str,
    source_id: str,
    final_url: str,
    observed_at: datetime,
    fetched_at: datetime,
    raw_html_hash: str,
    raw_html_path: str,
) -> CrawledNotice:

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    date_node = find_primary_date_node(
        soup
    )

    title = extract_title(
        soup,
        date_node,
    )

    publication_date = (
        parse_dut_datetime(
            str(date_node)
        )
        if date_node
        else None
    )

    raw_text, parse_mode = (
        extract_article_text(
            date_node,
            title,
        )
    )

    attachments = extract_attachments(
        soup,
        final_url,
    )

    external_match = (
        NOTICE_ID_RE.search(
            urlparse(final_url).path
        )
    )

    external_id = (
        external_match.group(1)
        if external_match
        else None
    )

    content_hash = build_content_hash(
        title=title,
        publication_date=publication_date,
        raw_text=raw_text,
        attachment_links=attachments,
    )

    return CrawledNotice(
        source_id=source_id,
        external_id=external_id,
        canonical_url=final_url,
        title=title,
        publication_date=publication_date,
        raw_text=raw_text,
        attachment_links=attachments,
        observed_at=observed_at,
        fetched_at=fetched_at,
        content_hash=content_hash,
        raw_html_hash=raw_html_hash,
        raw_html_path=raw_html_path,
        parse_mode=parse_mode,
    )