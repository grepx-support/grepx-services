"""Slot planning: consecutive slots of N minutes between start and end. Pure."""
from __future__ import annotations

MAX_CAPACITY = 500


class PlanError(ValueError):
    pass


def _minutes(hhmm: str) -> int:
    hour, minute = (int(x) for x in hhmm.split(":"))
    return hour * 60 + minute


def plan_slots(start: str, end: str, minutes: int, capacity: int) -> list[dict]:
    try:
        a, b, minutes, capacity = _minutes(start), _minutes(end), int(minutes), int(capacity)
    except (ValueError, AttributeError) as exc:
        raise PlanError("INVALID_PLAN") from exc
    if not (a < b and 5 <= minutes <= 240 and 1 <= capacity <= MAX_CAPACITY):
        raise PlanError("INVALID_PLAN")
    fmt = lambda m: f"{m // 60:02d}:{m % 60:02d}"  # noqa: E731
    return [{"starts_at": fmt(t), "ends_at": fmt(min(t + minutes, b)), "capacity": capacity} for t in range(a, b, minutes)]
