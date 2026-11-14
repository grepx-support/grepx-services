# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Shift times: "HH:MM" on a date; an end before the start runs past midnight."""
from __future__ import annotations

from datetime import date, datetime, timedelta


def hhmm(value) -> str:
    try:
        h, m = (int(x) for x in str(value).split(":"))
    except (TypeError, ValueError):
        raise ValueError("INVALID_TIME")
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("INVALID_TIME")
    return f"{h:02d}:{m:02d}"


def span(day: str, start: str, end: str) -> tuple[datetime, datetime]:
    d = date.fromisoformat(day)
    a = datetime.combine(d, datetime.strptime(start, "%H:%M").time())
    b = datetime.combine(d, datetime.strptime(end, "%H:%M").time())
    return a, (b if b > a else b + timedelta(days=1))


def paid_minutes(shift: dict) -> int:
    a, b = span(shift["date"], shift["start"], shift["end"])
    return max(0, int((b - a).total_seconds() // 60) - int(shift.get("break_min") or 0))


def week_of(day: str) -> tuple[date, date]:
    d = date.fromisoformat(day)
    monday = d - timedelta(days=d.weekday())
    return monday, monday + timedelta(days=6)
