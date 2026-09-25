from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.actionability.models import ActionabilityStatus
from app.models.obligation import DeadlineValue, TemporalPrecision


DUT_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")


def _current_time(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(DUT_TIMEZONE)
    if now.tzinfo is None:
        raise ValueError("now must include timezone information")
    return now.astimezone(DUT_TIMEZONE)


def _boundary(
    value: DeadlineValue,
    *,
    end_of_period: bool,
) -> datetime | None:
    """Return a trusted comparison boundary, or None when it is unsafe."""
    if value.normalized is None or value.precision == TemporalPrecision.UNKNOWN:
        return None

    try:
        value_timezone = ZoneInfo(value.timezone)
        if value.precision == TemporalPrecision.DATE:
            parsed_date = date.fromisoformat(value.normalized)
            boundary_date = parsed_date + timedelta(days=1) if end_of_period else parsed_date
            return datetime.combine(boundary_date, time.min, tzinfo=value_timezone)

        if value.precision == TemporalPrecision.DATETIME:
            parsed_datetime = datetime.fromisoformat(value.normalized)
            if parsed_datetime.tzinfo is None:
                return None
            return parsed_datetime
    except (ValueError, ZoneInfoNotFoundError):
        return None

    return None


def resolve_actionability(
    *,
    deadline: DeadlineValue | None = None,
    start: DeadlineValue | None = None,
    end: DeadlineValue | None = None,
    now: datetime | None = None,
) -> ActionabilityStatus:
    """Resolve actionability without using publication or notice temporal state.

    Current reviewed obligations expose a deadline/end value. ``start`` and
    ``end`` are accepted independently so explicit structured ranges can be
    handled without parsing raw notice text when the schema later provides them.
    """
    if deadline is None and start is None and end is None:
        return ActionabilityStatus.NO_DEADLINE

    current = _current_time(now)
    effective_end = end or deadline
    start_boundary = _boundary(start, end_of_period=False) if start else None
    end_boundary = _boundary(effective_end, end_of_period=True) if effective_end else None

    if start is not None and start_boundary is None:
        return ActionabilityStatus.UNKNOWN
    if effective_end is not None and end_boundary is None:
        return ActionabilityStatus.UNKNOWN
    if start_boundary is not None and end_boundary is not None and start_boundary > end_boundary:
        return ActionabilityStatus.UNKNOWN

    if start_boundary is not None and current < start_boundary:
        return ActionabilityStatus.UPCOMING
    if end_boundary is not None:
        # A date-only deadline remains active for its complete local calendar day.
        # A timestamp remains active at the exact timestamp and expires after it.
        if effective_end and effective_end.precision == TemporalPrecision.DATE:
            return ActionabilityStatus.EXPIRED if current >= end_boundary else ActionabilityStatus.ACTIVE
        return ActionabilityStatus.EXPIRED if current > end_boundary else ActionabilityStatus.ACTIVE

    # A known start without a known end cannot establish expiry.
    return ActionabilityStatus.NO_DEADLINE
