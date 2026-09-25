import pytest

from app.verification.comparator import FieldComparator
from app.verification.models import FieldMatchState
from app.models.obligation import ActionType

def test_compare_deadline():
    assert FieldComparator.compare_deadline("20/09/2026", "2026-09-20").state == FieldMatchState.MATCH
    assert FieldComparator.compare_deadline("25/09/2026", "2026-09-20").state == FieldMatchState.CONFLICT

def test_compare_normalized_iso_deadline():
    assert FieldComparator.compare_deadline("2026-09-30", "2026-09-30").state == FieldMatchState.MATCH
    assert FieldComparator.compare_deadline("2026-09-30", "2026-10-01").state == FieldMatchState.CONFLICT


def test_reviewed_normalized_deadline_overrides_raw_range_first_date():
    raw_range = "14/09/2026 đến 18/09/2026"
    assert FieldComparator.compare_deadline(
        "2026-09-18",
        raw_range,
        normalized_official="2026-09-18",
    ).state == FieldMatchState.MATCH
    assert FieldComparator.compare_deadline(
        "2026-09-19",
        raw_range,
        normalized_official="2026-09-18",
    ).state == FieldMatchState.CONFLICT


def test_deadline_raw_text_remains_the_fallback_without_reviewed_normalization():
    assert FieldComparator.compare_deadline(
        "2026-09-14",
        "14/09/2026 đến 18/09/2026",
    ).state == FieldMatchState.MATCH

@pytest.mark.parametrize("invalid", ["2026-99-99", "2026-13-01", "2026-04-31", "2026-02-29"])
def test_invalid_iso_deadlines_do_not_match(invalid):
    assert FieldComparator.compare_deadline(invalid, invalid).state == FieldMatchState.INSUFFICIENT_EVIDENCE

def test_leap_day_requires_a_real_leap_year():
    assert FieldComparator.compare_deadline("2024-02-29", "2024-02-29").state == FieldMatchState.MATCH

def test_compare_amount():
    assert FieldComparator.compare_amount("1.000.000 vnd", "1000000").state == FieldMatchState.MATCH
    assert FieldComparator.compare_amount("500.000", "1000000").state == FieldMatchState.CONFLICT

def test_compare_action():
    assert FieldComparator.compare_action("đóng tiền", ActionType.PAY).state == FieldMatchState.MATCH
    assert FieldComparator.compare_action("đóng tiền", ActionType.REGISTER).state == FieldMatchState.CONFLICT


def test_normalized_action_is_authoritative_over_raw_lexical_fallback():
    assert FieldComparator.compare_action(
        "nộp phí giữ xe",
        ActionType.SUBMIT,
        normalized_claimed=ActionType.PAY.value,
    ).state == FieldMatchState.CONFLICT
    assert FieldComparator.compare_action(
        "nộp hồ sơ",
        ActionType.SUBMIT,
        normalized_claimed=ActionType.SUBMIT.value,
    ).state == FieldMatchState.MATCH
    assert FieldComparator.compare_action(
        "nộp học phí",
        ActionType.PAY,
        normalized_claimed=ActionType.PAY.value,
    ).state == FieldMatchState.MATCH
    assert FieldComparator.compare_action(
        "nộp hồ sơ",
        ActionType.SUBMIT,
    ).state == FieldMatchState.MATCH
    
def test_compare_location():
    assert FieldComparator.compare_location("http://example.com", "Phòng Đào tạo").state == FieldMatchState.CONFLICT

def test_compare_audience():
    assert FieldComparator.compare_audience("all", True, []).state == FieldMatchState.MATCH
    assert FieldComparator.compare_audience("all", False, ["CNTT"]).state == FieldMatchState.INSUFFICIENT_EVIDENCE
