"""Small, testable monitor orchestration over the established crawler."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import httpx

from app.crawler.service import crawl_source
from app.monitoring.models import MonitorCycleResult, MonitorOutcome, SourceMonitorResult
from app.monitoring.repository import init_monitoring_tables, save_cycle, save_notice_events, save_result
from app.db.database import get_connection
from app.sources.repository import list_sources

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MonitoringService:
    """Runs sources sequentially: low concurrency is deliberate politeness."""
    def __init__(self, *, interval_seconds: int, raw_data_dir: Path, crawl: Callable[..., dict] = crawl_source, retrieval_sync: Callable[[], None] | None = None, conditional_probe: Callable[[str], tuple[bool, str | None, str | None]] | None = None):
        if interval_seconds < 300:
            raise ValueError("Monitoring interval must be at least five minutes.")
        self.interval_seconds = interval_seconds
        self.raw_data_dir = raw_data_dir
        self.crawl = crawl
        self.retrieval_sync = retrieval_sync
        self.conditional_probe = conditional_probe

    def run_once(self) -> MonitorCycleResult:
        init_monitoring_tables()
        started = utc_now()
        results: list[SourceMonitorResult] = []
        for source in (item for item in list_sources() if item.enabled):
            checked = utc_now()
            try:
                if self.conditional_probe is not None:
                    unchanged, etag, last_modified = self.conditional_probe(source.source_id)
                    if unchanged:
                        item = SourceMonitorResult(source_id=source.source_id, outcome=MonitorOutcome.UNCHANGED, checked_at=checked, unchanged=1, etag=etag, last_modified=last_modified)
                        save_result(item, interval_seconds=self.interval_seconds)
                        results.append(item)
                        continue
                with get_connection() as connection:
                    before = {row["notice_id"]: row["current_content_hash"] for row in connection.execute("SELECT notice_id, current_content_hash FROM notices WHERE source_id = ?", (source.source_id,))}
                stats = self.crawl(source.source_id, raw_data_dir=self.raw_data_dir)
                if stats.get("created", 0):
                    outcome = MonitorOutcome.NEW
                elif stats.get("updated", 0):
                    outcome = MonitorOutcome.UPDATED
                elif stats.get("failed", 0) and not (stats.get("unchanged", 0) or stats.get("duplicate", 0)):
                    outcome = MonitorOutcome.FAILED
                else:
                    outcome = MonitorOutcome.UNCHANGED
                item = SourceMonitorResult(source_id=source.source_id, outcome=outcome, checked_at=checked, created=stats.get("created", 0), updated=stats.get("updated", 0), unchanged=stats.get("unchanged", 0) + stats.get("duplicate", 0), failed=stats.get("failed", 0))
                if outcome in {MonitorOutcome.NEW, MonitorOutcome.UPDATED}:
                    with get_connection() as connection:
                        after = {row["notice_id"]: row["current_content_hash"] for row in connection.execute("SELECT notice_id, current_content_hash FROM notices WHERE source_id = ?", (source.source_id,))}
                    events = [
                        (notice_id, MonitorOutcome.NEW if notice_id not in before else MonitorOutcome.UPDATED)
                        for notice_id, fingerprint in after.items()
                        if notice_id not in before or before[notice_id] != fingerprint
                    ]
                    save_notice_events(events=events, observed_at=checked)
            except Exception as exc:
                logger.warning("Monitor source failed: %s", source.source_id, exc_info=True)
                item = SourceMonitorResult(source_id=source.source_id, outcome=MonitorOutcome.FAILED, checked_at=checked, failed=1, error=f"{type(exc).__name__}: {exc}")
            save_result(item, interval_seconds=self.interval_seconds)
            results.append(item)
        retrieval_updated = any(item.outcome in {MonitorOutcome.NEW, MonitorOutcome.UPDATED} for item in results)
        if retrieval_updated and self.retrieval_sync is not None:
            self.retrieval_sync()
        finished = utc_now()
        save_cycle(started_at=started, finished_at=finished, results=results, retrieval_updated=retrieval_updated)
        return MonitorCycleResult(started_at=started, finished_at=finished, results=results, retrieval_updated=retrieval_updated)

    def run_forever(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.interval_seconds)


def conditional_listing_probe(source_id: str) -> tuple[bool, str | None, str | None]:
    """Use validators where a source supports them; 304 avoids parsing."""
    from app.monitoring.repository import get_status
    from app.sources.repository import get_source
    source = get_source(source_id)
    if source is None:
        raise ValueError(f"Unknown source: {source_id}")
    state = next((item for item in get_status(enabled=True).sources if item.source_id == source_id), None)
    headers = {"User-Agent": "UniTrust-V2-Monitor/0.1"}
    if state and state.etag:
        headers["If-None-Match"] = state.etag
    if state and state.last_modified:
        headers["If-Modified-Since"] = state.last_modified
    with httpx.Client(timeout=httpx.Timeout(15.0, connect=5.0), follow_redirects=True, headers=headers, trust_env=False) as client:
        response = client.get(source.listing_url)
    if len(response.content) > 2_000_000:
        raise ValueError("Listing response exceeds monitor size limit")
    if response.status_code != 304:
        response.raise_for_status()
    return response.status_code == 304, response.headers.get("etag"), response.headers.get("last-modified")
