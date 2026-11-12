"""
Timezone helpers (Part 17 control #6).

- All storage is UTC.
- All reporting/display uses the company timezone.
- Half-open ranges: [start, end).
- Never add fixed UTC offsets; never assume 24-hour days (DST-safe).
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings


def company_tz() -> ZoneInfo:
    return ZoneInfo(settings.COMPANY_DEFAULT_TIMEZONE)


def now_company() -> datetime:
    return datetime.now(tz=company_tz())


def company_day_range_utc(d: date) -> tuple[datetime, datetime]:
    """Return [start_utc, end_utc) for a given company-local calendar day."""
    tz = company_tz()
    start_local = datetime.combine(d, time.min, tzinfo=tz)
    end_local = datetime.combine(d + timedelta(days=1), time.min, tzinfo=tz)
    return (start_local.astimezone(ZoneInfo("UTC")),
            end_local.astimezone(ZoneInfo("UTC")))


def company_week_range_utc(d: date) -> tuple[datetime, datetime]:
    """Monday-start week containing `d`, as UTC half-open range."""
    tz = company_tz()
    monday = d - timedelta(days=d.weekday())
    start_local = datetime.combine(monday, time.min, tzinfo=tz)
    end_local = datetime.combine(monday + timedelta(days=7), time.min, tzinfo=tz)
    return (start_local.astimezone(ZoneInfo("UTC")),
            end_local.astimezone(ZoneInfo("UTC")))
