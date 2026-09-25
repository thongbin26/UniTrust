from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class SourceType(StrEnum):
    CENTRAL = "official_central"
    STUDENT_AFFAIRS = "student_affairs"
    STUDENT_PORTAL = "official_student_portal"
    ACADEMIC = "academic"
    FINANCE = "official_finance"
    FACULTY = "faculty"
    REFERENCE = "official_reference"
    SOCIAL = "official_social_supplementary"


class SourceHealthStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class SourceSeed(BaseModel):
    source_id: str
    name: str

    source_type: SourceType

    base_url: str
    listing_url: str

    official_domain: str
    is_official: bool = True

    expected_marker: str | None = None
    provenance_note: str
    authority_scope: str = "university-wide"
    enabled: bool = True
    crawl_method: str = "dut_html"
    notes: str = ""


class SourceRead(SourceSeed):
    health_status: SourceHealthStatus = SourceHealthStatus.UNKNOWN

    last_checked_at: datetime | None = None
    last_success_at: datetime | None = None

    last_http_status: int | None = None
    last_error: str | None = None


class SourceSnapshot(BaseModel):
    snapshot_id: int | None = None

    source_id: str

    observed_at: datetime
    fetched_at: datetime

    final_url: str | None = None
    http_status: int | None = None

    content_hash: str | None = None
    content_length: int = 0


class SourceCheckResult(BaseModel):
    source_id: str
    name: str

    health_status: SourceHealthStatus

    checked_at: datetime

    http_status: int | None = None
    final_url: str | None = None

    content_hash: str | None = None
    content_length: int = 0

    error: str | None = None
