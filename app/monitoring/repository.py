"""Persistence for V2 monitor state.

These tables are intentionally initialized only by the opt-in monitor.  This
keeps the frozen RC database byte-stable during ordinary application startup.
"""
from datetime import datetime, timedelta, timezone

from app.db.database import get_connection
from app.monitoring.models import MonitorOutcome, MonitorStatus, SourceMonitorResult, SourceMonitorState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def init_monitoring_tables() -> None:
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS source_monitor_state (
                source_id TEXT PRIMARY KEY,
                last_checked_at TEXT,
                last_changed_at TEXT,
                last_error_at TEXT,
                last_error TEXT,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                last_outcome TEXT,
                next_check_at TEXT,
                etag TEXT,
                last_modified TEXT,
                FOREIGN KEY(source_id) REFERENCES sources(source_id)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS monitor_notice_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                notice_id INTEGER NOT NULL,
                outcome TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                UNIQUE(notice_id, outcome, observed_at),
                FOREIGN KEY(notice_id) REFERENCES notices(notice_id)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS monitor_cycles (
                cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                new_count INTEGER NOT NULL,
                updated_count INTEGER NOT NULL,
                unchanged_count INTEGER NOT NULL,
                failed_count INTEGER NOT NULL,
                retrieval_updated INTEGER NOT NULL DEFAULT 0
            )
        """)
        connection.commit()


def save_result(result: SourceMonitorResult, *, interval_seconds: int) -> None:
    failures = 1 if result.outcome == MonitorOutcome.FAILED else 0
    # Bounded exponential backoff prevents a failed source from being hammered.
    delay = min(interval_seconds * (2 ** min(failures, 4)), interval_seconds * 16)
    with get_connection() as connection:
        prior = connection.execute(
            "SELECT consecutive_failures FROM source_monitor_state WHERE source_id = ?",
            (result.source_id,),
        ).fetchone()
        consecutive = (int(prior["consecutive_failures"]) + 1) if (prior and failures) else failures
        delay = min(interval_seconds * (2 ** min(consecutive, 4)), interval_seconds * 16)
        changed_at = result.checked_at.isoformat() if result.outcome in {MonitorOutcome.NEW, MonitorOutcome.UPDATED} else None
        error_at = result.checked_at.isoformat() if failures else None
        next_check = result.checked_at + timedelta(seconds=delay)
        connection.execute("""
            INSERT INTO source_monitor_state (
                source_id, last_checked_at, last_changed_at, last_error_at,
                last_error, consecutive_failures, last_outcome, next_check_at, etag, last_modified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                last_checked_at = excluded.last_checked_at,
                last_changed_at = COALESCE(excluded.last_changed_at, source_monitor_state.last_changed_at),
                last_error_at = excluded.last_error_at,
                last_error = excluded.last_error,
                consecutive_failures = excluded.consecutive_failures,
                last_outcome = excluded.last_outcome,
                next_check_at = excluded.next_check_at,
                etag = COALESCE(excluded.etag, source_monitor_state.etag),
                last_modified = COALESCE(excluded.last_modified, source_monitor_state.last_modified)
        """, (
            result.source_id, result.checked_at.isoformat(), changed_at, error_at,
            result.error, consecutive, result.outcome.value, next_check.isoformat(),
            result.etag, result.last_modified,
        ))
        connection.commit()


def save_notice_events(*, events: list[tuple[int, MonitorOutcome]], observed_at: datetime) -> None:
    if not events:
        return
    with get_connection() as connection:
        connection.executemany(
            "INSERT OR IGNORE INTO monitor_notice_events (notice_id, outcome, observed_at) VALUES (?, ?, ?)",
            [(notice_id, outcome.value, observed_at.isoformat()) for notice_id, outcome in events],
        )
        connection.commit()


def latest_notice_activity() -> dict[int, str]:
    """Best available monitor classification; absent means no claimed activity."""
    try:
        with get_connection() as connection:
            cutoff = (utc_now() - timedelta(hours=48)).isoformat()
            rows = connection.execute("""
                SELECT event.notice_id, event.outcome
                FROM monitor_notice_events AS event
                JOIN (
                    SELECT notice_id, MAX(event_id) AS event_id
                    FROM monitor_notice_events GROUP BY notice_id
                ) AS latest ON latest.event_id = event.event_id
                WHERE event.observed_at >= ?
            """, (cutoff,)).fetchall()
    except Exception:
        return {}
    return {int(row["notice_id"]): row["outcome"] for row in rows}


def backfill_recent_notice_events() -> None:
    """Recover V2 event metadata when a monitor-state migration is introduced.

    It only derives events from a recent persisted NEW/UPDATED source outcome,
    the notice's observation timestamp, and retained version count. It never
    labels bootstrap-only rows or creates a notice/version.
    """
    cutoff = (utc_now() - timedelta(hours=48)).isoformat()
    with get_connection() as connection:
        sources = connection.execute("""
            SELECT source_id, last_outcome, last_changed_at
            FROM source_monitor_state
            WHERE last_outcome IN ('NEW', 'UPDATED')
              AND last_changed_at >= ?
        """, (cutoff,)).fetchall()
        candidates: list[tuple[int, MonitorOutcome, str]] = []
        for source in sources:
            rows = connection.execute("""
                SELECT n.notice_id, n.last_observed_at, COUNT(v.version_id) AS version_count
                FROM notices AS n JOIN notice_versions AS v ON v.notice_id = n.notice_id
                WHERE n.source_id = ? AND n.last_observed_at >= ?
                GROUP BY n.notice_id
            """, (source["source_id"], source["last_changed_at"])).fetchall()
            for row in rows:
                outcome = MonitorOutcome.UPDATED if int(row["version_count"]) > 1 else MonitorOutcome.NEW
                candidates.append((int(row["notice_id"]), outcome, row["last_observed_at"]))
        connection.executemany(
            "INSERT OR IGNORE INTO monitor_notice_events (notice_id, outcome, observed_at) VALUES (?, ?, ?)",
            [(notice_id, outcome.value, observed_at) for notice_id, outcome, observed_at in candidates],
        )
        connection.commit()


def save_cycle(*, started_at: datetime, finished_at: datetime, results: list[SourceMonitorResult], retrieval_updated: bool) -> None:
    totals = {outcome: sum(item.outcome == outcome for item in results) for outcome in MonitorOutcome}
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO monitor_cycles (
                started_at, finished_at, new_count, updated_count, unchanged_count,
                failed_count, retrieval_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (started_at.isoformat(), finished_at.isoformat(), totals[MonitorOutcome.NEW], totals[MonitorOutcome.UPDATED], totals[MonitorOutcome.UNCHANGED], totals[MonitorOutcome.FAILED], int(retrieval_updated)))
        connection.commit()


def get_status(*, enabled: bool) -> MonitorStatus:
    if not enabled:
        return MonitorStatus(enabled=False)
    init_monitoring_tables()
    backfill_recent_notice_events()
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM source_monitor_state ORDER BY source_id").fetchall()
        last_cycle = connection.execute("SELECT * FROM monitor_cycles ORDER BY cycle_id DESC LIMIT 1").fetchone()
    states = [SourceMonitorState.model_validate(dict(row)) for row in rows]
    healthy = sum(state.last_outcome != MonitorOutcome.FAILED for state in states)
    changed = [state.last_changed_at for state in states if state.last_changed_at]
    return MonitorStatus(
        enabled=True, monitored_sources=len(states), healthy_sources=healthy,
        degraded_or_failed_sources=len(states) - healthy,
        last_global_check=(last_cycle["finished_at"] if last_cycle else None),
        last_successful_update=max(changed) if changed else None,
        recent_new=(last_cycle["new_count"] if last_cycle else 0),
        recent_updated=(last_cycle["updated_count"] if last_cycle else 0),
        sources=states,
    )
