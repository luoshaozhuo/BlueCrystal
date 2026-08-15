"""Time utilities for deterministic scenario processing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def ensure_utc(dt: datetime) -> datetime:
    """Normalize a datetime value to timezone-aware UTC.

    Args:
        dt: Datetime value that may be naive or timezone-aware.

    Returns:
        The same instant represented as a UTC-aware datetime.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_iso_datetime(value: str) -> datetime:
    """Parse an ISO 8601 datetime string into UTC.

    Args:
        value: ISO datetime string, optionally ending with `Z`.

    Returns:
        Parsed UTC-aware datetime.
    """
    normalized = value.replace("Z", "+00:00")
    return ensure_utc(datetime.fromisoformat(normalized))


def max_datetime(
    left: datetime | None,
    right: datetime | None,
) -> datetime | None:
    """Return the newer value between two optional datetimes in UTC."""

    if left is None:
        return right

    if right is None:
        return left

    return max(ensure_utc(left), ensure_utc(right))


def floor_to_second(dt: datetime) -> datetime:
    """Floor a datetime to second resolution in UTC.

    Args:
        dt: Datetime value to normalize.

    Returns:
        UTC datetime with microseconds cleared.
    """
    dt_utc = ensure_utc(dt)
    return dt_utc.replace(microsecond=0)


def floor_to_minute(dt: datetime) -> datetime:
    """Floor a datetime to minute resolution in UTC.

    Args:
        dt: Datetime value to normalize.

    Returns:
        UTC datetime with seconds and microseconds cleared.
    """
    dt_utc = ensure_utc(dt)
    return dt_utc.replace(second=0, microsecond=0)


def window_start(end_time: datetime, seconds: int) -> datetime:
    """Return the inclusive UTC start of a backward-looking time window.

    Args:
        end_time: Inclusive UTC window end.
        seconds: Window size in seconds.

    Returns:
        Inclusive UTC window start.
    """
    return ensure_utc(end_time) - timedelta(seconds=seconds)
