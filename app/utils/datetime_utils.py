"""Date and time utilities."""

from datetime import datetime, timedelta
from typing import Optional
import pytz

from app.core.config import settings


def get_current_time() -> datetime:
    """Get current time in configured timezone.

    Returns:
        Current datetime in application timezone
    """
    tz = pytz.timezone(settings.scheduler.timezone)
    return datetime.now(tz)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string.

    Args:
        dt: Datetime to format
        format_str: Format string

    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse datetime string.

    Args:
        dt_str: Datetime string
        format_str: Format string

    Returns:
        Parsed datetime object
    """
    return datetime.strptime(dt_str, format_str)


def get_date_range(days_back: int = 1) -> tuple[datetime, datetime]:
    """Get date range from days back to now.

    Args:
        days_back: Number of days to go back

    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = get_current_time()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date
