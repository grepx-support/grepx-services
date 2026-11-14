# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Balance of one person for one leave type in one year: this year's allowance (pro-rated by the months worked when
they started this year) plus what was carried over from last year (up to the type's limit), minus approved days;
pending days are shown apart, and a request may not go past what is left (unless the type is unlimited)."""
from __future__ import annotations

from datetime import date


def allowance(kind: dict, year: int, started: str = "") -> float:
    days = float(kind.get("days_per_year") or 0)
    if started and started[:4] == str(year):
        months_left = 12 - date.fromisoformat(started[:10]).month + 1
        return round(days * months_left / 12 * 2) / 2          # to the nearest half day
    if started and started[:4] > str(year):
        return 0.0
    return days


def used(leaves: list[dict], type_id: str, year: int, state: str) -> float:
    return sum(float(l.get("days") or 0) for l in leaves if l.get("type_id") == type_id and l.get("state") == state
               and str(l.get("first", ""))[:4] == str(year))


def balance(kind: dict, leaves: list[dict], year: int, started: str = "") -> dict:
    tid = kind["type_id"]
    last_left = allowance(kind, year - 1, started) - used(leaves, tid, year - 1, "approved")
    carried = max(0.0, min(float(kind.get("carry_over") or 0), last_left)) if not (started and started[:4] >= str(year)) else 0.0
    total = allowance(kind, year, started) + carried
    taken, pending = used(leaves, tid, year, "approved"), used(leaves, tid, year, "pending")
    return {"type_id": tid, "name": kind["name"], "paid": kind.get("paid", True), "unlimited": kind.get("unlimited", False),
            "allowance": total, "carried": carried, "taken": taken, "pending": pending, "left": total - taken - pending}
