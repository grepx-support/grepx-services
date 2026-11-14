# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Clocking in and out against the roster: which shift it belongs to, late arrival, minutes worked."""
from __future__ import annotations

from datetime import datetime

from .times import span

GRACE_MIN = 5


def shift_for(shifts: list[dict], at: datetime) -> dict | None:
    """The person's shift running now, or starting within the next 2 hours, or ended in the last hour."""
    best, gap = None, None
    for s in shifts:
        a, b = span(s["date"], s["start"], s["end"])
        if (a - at).total_seconds() > 7200 or (at - b).total_seconds() > 3600:
            continue
        g = abs((a - at).total_seconds())
        if gap is None or g < gap:
            best, gap = s, g
    return best


def late_minutes(shift: dict | None, clock_in: datetime) -> int:
    if not shift:
        return 0
    a, _ = span(shift["date"], shift["start"], shift["end"])
    late = int((clock_in - a).total_seconds() // 60)
    return late if late > GRACE_MIN else 0


def worked_minutes(clock_in: datetime, clock_out: datetime, break_min: int = 0) -> int:
    return max(0, int((clock_out - clock_in).total_seconds() // 60) - int(break_min or 0))
