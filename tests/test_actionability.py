from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.actionability import ActionabilityStatus, DUT_TIMEZONE, resolve_actionability
from app.models.obligation import CanonicalNoticeAnnotation, DeadlineValue, TemporalPrecision
from frontend.for_you_presenter import group_visible_obligations, is_visible_obligation


NOW = datetime(2026, 9, 20, 12, 0, tzinfo=DUT_TIMEZONE)


def temporal_value(value: str | None, precision: TemporalPrecision = TemporalPrecision.DATE) -> DeadlineValue:
    return DeadlineValue(
        raw_text=value or "không chuẩn hóa được",
        normalized=value,
        precision=precision,
        timezone="Asia/Ho_Chi_Minh",
    )


@pytest.mark.parametrize(
    ("deadline", "expected"),
    [
        ("2026-09-19", ActionabilityStatus.EXPIRED),
        ("2026-09-20", ActionabilityStatus.ACTIVE),
        ("2026-09-21", ActionabilityStatus.ACTIVE),
    ],
)
def test_date_deadline_relative_to_today(deadline, expected):
    assert resolve_actionability(deadline=temporal_value(deadline), now=NOW) == expected


def test_future_start_is_upcoming():
    assert resolve_actionability(start=temporal_value("2026-09-21"), now=NOW) == ActionabilityStatus.UPCOMING


def test_active_range():
    assert resolve_actionability(
        start=temporal_value("2026-09-19"),
        end=temporal_value("2026-09-21"),
        now=NOW,
    ) == ActionabilityStatus.ACTIVE


def test_finished_range_is_expired():
    assert resolve_actionability(
        start=temporal_value("2026-09-18"),
        end=temporal_value("2026-09-19"),
        now=NOW,
    ) == ActionabilityStatus.EXPIRED


def test_no_deadline_is_no_deadline():
    assert resolve_actionability(now=NOW) == ActionabilityStatus.NO_DEADLINE


def test_unparseable_deadline_is_unknown():
    unknown = temporal_value(None, TemporalPrecision.UNKNOWN)
    assert resolve_actionability(deadline=unknown, now=NOW) == ActionabilityStatus.UNKNOWN


def test_date_deadline_uses_ho_chi_minh_calendar_boundary():
    before_local_midnight = datetime(2026, 9, 20, 16, 59, tzinfo=timezone.utc)
    after_local_midnight = datetime(2026, 9, 20, 17, 1, tzinfo=timezone.utc)
    deadline = temporal_value("2026-09-20")
    assert resolve_actionability(deadline=deadline, now=before_local_midnight) == ActionabilityStatus.ACTIVE
    assert resolve_actionability(deadline=deadline, now=after_local_midnight) == ActionabilityStatus.EXPIRED


def test_datetime_expires_only_after_exact_timestamp():
    deadline = temporal_value("2026-09-20T16:00:00+07:00", TemporalPrecision.DATETIME)
    exact = datetime(2026, 9, 20, 16, 0, tzinfo=DUT_TIMEZONE)
    assert resolve_actionability(deadline=deadline, now=exact) == ActionabilityStatus.ACTIVE
    assert resolve_actionability(deadline=deadline, now=exact.replace(microsecond=1)) == ActionabilityStatus.EXPIRED


def obligation_item(actionability, applicability="APPLIES"):
    return {
        "action_text": f"item-{actionability}",
        "actionability_status": actionability,
        "applicability": {"status": applicability},
    }


def test_expired_is_hidden_but_unknown_and_no_deadline_remain_visible():
    expired = obligation_item("EXPIRED")
    unknown = obligation_item("UNKNOWN")
    no_deadline = obligation_item("NO_DEADLINE")
    assert not is_visible_obligation(expired)
    assert is_visible_obligation(unknown)
    assert is_visible_obligation(no_deadline)


def test_visible_group_counts_exclude_expired_items():
    items = [
        obligation_item("ACTIVE"),
        obligation_item("EXPIRED"),
        obligation_item("UNKNOWN", "UNKNOWN"),
        obligation_item("NO_DEADLINE", "DOES_NOT_APPLY"),
    ]
    groups = group_visible_obligations(items)
    assert {name: len(group) for name, group in groups.items()} == {
        "APPLIES": 1,
        "UNKNOWN": 1,
        "DOES_NOT_APPLY": 1,
    }


def test_missing_actionability_fails_safe_and_stays_visible():
    assert is_visible_obligation({"applicability": {"status": "UNKNOWN"}})


def load_reviewed(name: str) -> CanonicalNoticeAnnotation:
    path = Path(__file__).resolve().parents[1] / "data/annotations/batch_001" / name
    return CanonicalNoticeAnnotation.model_validate_json(path.read_text(encoding="utf-8"))


def test_existing_reviewed_obligations_cover_expired_active_and_no_deadline():
    expired = load_reviewed("01_notice_1.json").obligations[0]
    active = load_reviewed("02_notice_3.json").obligations[0]
    no_deadline = load_reviewed("04_notice_2.json").obligations[0]
    assert resolve_actionability(deadline=expired.deadline, now=NOW) == ActionabilityStatus.EXPIRED
    assert resolve_actionability(deadline=active.deadline, now=NOW) == ActionabilityStatus.ACTIVE
    assert resolve_actionability(deadline=no_deadline.deadline, now=NOW) == ActionabilityStatus.NO_DEADLINE
