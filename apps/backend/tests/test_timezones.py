"""Part 17 control #6 — timezone correctness."""
from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

from apps.core.timezones import (
    company_day_range_utc,
    company_week_range_utc,
    company_tz,
)


def test_company_day_range_is_half_open_and_utc() -> None:
    start, end = company_day_range_utc(date(2026, 3, 29))  # IST has no DST, but verify general shape
    assert start.tzinfo == ZoneInfo("UTC")
    assert end.tzinfo == ZoneInfo("UTC")
    assert end > start
    # 24h in IST = 24h in UTC for this TZ (IST never shifts)
    assert (end - start).total_seconds() == 24 * 3600


def test_week_range_starts_on_monday() -> None:
    # Wednesday 2026-04-01
    start, end = company_week_range_utc(date(2026, 4, 1))
    # Convert back to company TZ to confirm Monday start
    monday_local = start.astimezone(company_tz()).date()
    assert monday_local.weekday() == 0
    assert (end - start).days == 7
