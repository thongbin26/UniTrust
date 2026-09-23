from datetime import datetime, timezone
from pathlib import Path

from app.db.database import init_database
from app.monitoring.models import MonitorOutcome
from app.monitoring.repository import get_status, latest_notice_activity, save_notice_events
from app.monitoring.service import MonitoringService
from app.sources.repository import seed_sources


def test_monitor_cycle_classifies_new_then_unchanged_without_retrieval_work(tmp_path):
    init_database()
    seed_sources()
    calls = []

    def new_crawl(source_id, **_kwargs):
        calls.append(source_id)
        return {"created": 1, "updated": 0, "unchanged": 0, "duplicate": 0, "failed": 0}

    retrieval = []
    service = MonitoringService(interval_seconds=300, raw_data_dir=tmp_path / "raw", crawl=new_crawl, retrieval_sync=lambda: retrieval.append("sync"))
    first = service.run_once()
    assert {item.outcome for item in first.results} == {MonitorOutcome.NEW}
    assert retrieval == ["sync"]

    service.crawl = lambda source_id, **_kwargs: {"created": 0, "updated": 0, "unchanged": 1, "duplicate": 0, "failed": 0}
    second = service.run_once()
    assert {item.outcome for item in second.results} == {MonitorOutcome.UNCHANGED}
    assert retrieval == ["sync"]


def test_monitor_change_and_failure_are_isolated_and_failure_recovers(tmp_path):
    init_database()
    seed_sources()
    source_calls = []

    def mixed(source_id, **_kwargs):
        source_calls.append(source_id)
        if source_id == "dut_academic":
            raise RuntimeError("offline fixture failure")
        if source_id == "dut_ctsv":
            return {"created": 0, "updated": 1, "unchanged": 0, "duplicate": 0, "failed": 0}
        return {"created": 0, "updated": 0, "unchanged": 1, "duplicate": 0, "failed": 0}

    service = MonitoringService(interval_seconds=300, raw_data_dir=tmp_path / "raw", crawl=mixed, retrieval_sync=lambda: None)
    result = service.run_once()
    outcomes = {item.source_id: item.outcome for item in result.results}
    assert outcomes["dut_ctsv"] == MonitorOutcome.UPDATED
    assert outcomes["dut_academic"] == MonitorOutcome.FAILED
    assert len(source_calls) == 7
    status = get_status(enabled=True)
    failed = next(item for item in status.sources if item.source_id == "dut_academic")
    assert failed.consecutive_failures == 1

    service.crawl = lambda source_id, **_kwargs: {"created": 0, "updated": 0, "unchanged": 1, "duplicate": 0, "failed": 0}
    service.run_once()
    recovered = next(item for item in get_status(enabled=True).sources if item.source_id == "dut_academic")
    assert recovered.consecutive_failures == 0
    assert recovered.last_outcome == MonitorOutcome.UNCHANGED


def test_conditional_not_modified_skips_crawl(tmp_path):
    init_database()
    seed_sources()
    crawled = []
    service = MonitoringService(
        interval_seconds=300, raw_data_dir=tmp_path / "raw",
        crawl=lambda source_id, **_kwargs: crawled.append(source_id) or {},
        conditional_probe=lambda _source_id: (True, '"fixture-etag"', "Wed, 01 Jan 2026 00:00:00 GMT"),
    )
    result = service.run_once()
    assert all(item.outcome == MonitorOutcome.UNCHANGED for item in result.results)
    assert crawled == []


def test_monitor_status_emits_timezone_aware_next_check(tmp_path):
    init_database()
    seed_sources()
    service = MonitoringService(interval_seconds=300, raw_data_dir=tmp_path / "raw", crawl=lambda _source_id, **_kwargs: {})
    service.run_once()
    state = get_status(enabled=True).sources[0]
    assert state.next_check_at is not None
    assert state.next_check_at.tzinfo is not None


def test_persisted_notice_activity_only_exposes_new_or_updated_events():
    init_database()
    seed_sources()
    now = datetime.now(timezone.utc)
    save_notice_events(events=[(1, MonitorOutcome.NEW), (2, MonitorOutcome.UPDATED)], observed_at=now)
    activity = latest_notice_activity()
    assert activity[1] == "NEW"
    assert activity[2] == "UPDATED"
    assert 3 not in activity
