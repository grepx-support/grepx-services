# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""How many days a leave takes: every day from the first to the last, except the business's weekly days off
(Sunday unless the business says otherwise); a half day counts 0.5."""
from __future__ import annotations

from datetime import date, timedelta


def parse(value) -> date:
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise ValueError("INVALID_DATE")


def leave_days(first: date, last: date, half: bool = False, days_off: tuple[int, ...] = (6,)) -> float:
    if last < first:
        raise ValueError("INVALID_DATE")
    n = sum(1 for i in range((last - first).days + 1) if (first + timedelta(days=i)).weekday() not in days_off)
    return 0.5 if half and n == 1 else float(n)


def overlaps(a_first: str, a_last: str, b_first: str, b_last: str) -> bool:
    return a_first <= b_last and b_first <= a_last
