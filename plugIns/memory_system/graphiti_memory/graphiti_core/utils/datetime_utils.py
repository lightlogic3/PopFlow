
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Returns the current UTC datetime with timezone information."""
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime | None) -> datetime | None:
    """
    Ensures a datetime is timezone-aware and in UTC.
    If the datetime is naive (no timezone), assumes it's in UTC.
    If the datetime has a different timezone, converts it to UTC.
    Returns None if input is None.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # If datetime is naive, assume it's UTC
        return dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        # If datetime has a different timezone, convert to UTC
        return dt.astimezone(timezone.utc)

    return dt
