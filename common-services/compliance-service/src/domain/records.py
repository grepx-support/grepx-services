# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A record of a check: a reading is in range or not; a checklist passes when every item is answered yes. A failed
record must say what was done about it (the corrective action inspectors look for). What is due today."""
from __future__ import annotations


def judge(point: dict, raw: dict) -> dict:
    if point["kind"] == "reading":
        try:
            value = float(raw.get("value"))
        except (TypeError, ValueError):
            raise ValueError("INVALID_VALUE")
        ok = (point.get("min") is None or value >= point["min"]) and (point.get("max") is None or value <= point["max"])
        return {"value": value, "ok": ok}
    answers = {str(k): bool(v) for k, v in (raw.get("answers") or {}).items() if str(k) in point["questions"]}
    if set(answers) != set(point["questions"]):
        raise ValueError("INVALID_VALUE")
    return {"answers": answers, "ok": all(answers.values()), "failed": [i for i in point["questions"] if not answers[i]]}


def due(point: dict, done_today: int, done_this_week: int) -> int:
    """How many more records this check needs today."""
    if point["every"] == "weekly":
        return 0 if done_this_week else 1
    return max(0, {"twice_daily": 2, "daily": 1}[point["every"]] - done_today)
