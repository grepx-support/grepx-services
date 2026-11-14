# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What a check is: a reading (a number in a unit, safe between min and / or max) or a checklist (questions answered
yes / no); how many times a day it is due (or once a week)."""
from __future__ import annotations

KINDS = ("reading", "checklist")
FREQUENCY = {"twice_daily": 2, "daily": 1, "weekly": 0}        # records expected per day (weekly: one in 7 days)


def _number(value, reason: str = "INVALID_RANGE") -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(reason)


def clean_point(raw: dict) -> dict:
    name = " ".join(str(raw.get("name") or "").split())[:60]
    if not name:
        raise ValueError("INVALID_NAME")
    kind = str(raw.get("kind") or "reading")
    if kind not in KINDS:
        raise ValueError("INVALID_KIND")
    low, high = _number(raw.get("min")), _number(raw.get("max"))
    if kind == "reading" and (low is None and high is None or low is not None and high is not None and low > high):
        raise ValueError("INVALID_RANGE")
    questions = [" ".join(str(i).split())[:120] for i in raw.get("questions") or [] if str(i).strip()]
    if kind == "checklist" and not questions:
        raise ValueError("INVALID_KIND")
    every = str(raw.get("every") or "daily")
    if every not in FREQUENCY:
        raise ValueError("INVALID_KIND")
    return {"name": name, "kind": kind, "unit": " ".join(str(raw.get("unit") or "").split())[:12], "min": low, "max": high,
            "questions": questions if kind == "checklist" else [], "every": every, "group": " ".join(str(raw.get("group") or "").split())[:40]}
