# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What a valid shift is and when two shifts clash (the same person cannot be in two places at once - any site)."""
from __future__ import annotations

from datetime import date

from .times import hhmm, span


def clean_shift(raw: dict) -> dict:
    try:
        day = date.fromisoformat(str(raw.get("date") or "")[:10]).isoformat()
    except ValueError:
        raise ValueError("INVALID_DATE")
    start, end = hhmm(raw.get("start")), hhmm(raw.get("end"))
    if start == end:
        raise ValueError("INVALID_TIME")
    try:
        brk = int(float(raw.get("break_min") or 0))
    except (TypeError, ValueError):
        raise ValueError("INVALID_TIME")
    if not str(raw.get("site_id") or ""):
        raise ValueError("MISSING_SITE")
    return {"date": day, "start": start, "end": end, "break_min": max(0, min(brk, 240)), "site_id": str(raw["site_id"]),
            "employee_id": str(raw.get("employee_id") or ""), "role": " ".join(str(raw.get("role") or "").split())[:40],
            "note": str(raw.get("note") or "")[:200]}


def clashes(shift: dict, others: list[dict]) -> list[dict]:
    """The person's other shifts that overlap this one (open shifts - nobody yet - never clash)."""
    if not shift.get("employee_id"):
        return []
    a, b = span(shift["date"], shift["start"], shift["end"])
    out = []
    for o in others:
        if o.get("employee_id") != shift["employee_id"] or o.get("shift_id") == shift.get("shift_id"):
            continue
        c, d = span(o["date"], o["start"], o["end"])
        if a < d and c < b:
            out.append(o)
    return out
