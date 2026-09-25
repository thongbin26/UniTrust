from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class MonitorOutcome(StrEnum):
    NEW = "NEW"
    UPDATED = "UPDATED"
    UNCHANGED = "UNCHANGED"
    FAILED = "FAILED"


class SourceMonitorState(BaseModel):
    source_id: str
    last_checked_at: datetime | None = None
    last_changed_at: datetime | None = None
    last_error_at: datetime | None = None
    last_error: str | None = None
    consecutive_failures: int = 0
    last_outcome: MonitorOutcome | None = None
    next_check_at: datetime | None = None
    etag: str | None = None
    last_modified: str | None = None

    @field_validator("last_checked_at", "last_changed_at", "last_error_at", "next_check_at", mode="after")
    @classmethod
    def normalize_legacy_naive_timestamps(cls, value: datetime | None) -> datetime | None:
        # Early V2 dev rows used SQLite datetime() and were UTC but naïve.
        # The API never emits an ambiguous timestamp.
        return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value


class SourceMonitorResult(BaseModel):
    source_id: str
    outcome: MonitorOutcome
    checked_at: datetime
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    failed: int = 0
    error: str | None = None
    etag: str | None = None
    last_modified: str | None = None


class MonitorCycleResult(BaseModel):
    started_at: datetime
    finished_at: datetime
    results: list[SourceMonitorResult] = Field(default_factory=list)
    retrieval_updated: bool = False


class MonitorStatus(BaseModel):
    enabled: bool
    monitored_sources: int = 0
    healthy_sources: int = 0
    degraded_or_failed_sources: int = 0
    last_global_check: datetime | None = None
    last_successful_update: datetime | None = None
    recent_new: int = 0
    recent_updated: int = 0
    sources: list[SourceMonitorState] = Field(default_factory=list)
