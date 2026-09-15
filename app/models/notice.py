from datetime import datetime

from pydantic import BaseModel


class NoticeLink(BaseModel):
    url: str
    external_id: str | None = None


class CrawledNotice(BaseModel):
    source_id: str
    external_id: str | None = None

    canonical_url: str
    title: str

    publication_date: datetime | None = None

    raw_text: str
    attachment_links: list[str] = []

    observed_at: datetime
    fetched_at: datetime

    content_hash: str
    raw_html_hash: str
    raw_html_path: str

    parse_mode: str