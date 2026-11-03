# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Event report numbers from plain rows: the booking funnel, show and fill rate, slots, messages, tasks. Pure.
Product figures (e.g. units donated, blood groups) are added by the product's event_report plugin."""
from collections import Counter


def _pct(a: int, b: int) -> int:
    return round(100 * a / b) if b else 0


def build_stats(event: dict, bookings: list[dict], slots: list[dict], notes: list[dict], tasks: list[dict]) -> dict:
    """bookings: the event's bookings; notes: messages sent about the event; tasks: the event's tasks."""
    people = [r for r in bookings if r.get("state") != "cancelled"]
    status = Counter(r.get("state") for r in people)
    attended = [r for r in people if r.get("state") == "attended"]
    booked = sum(1 for r in people if r.get("state") not in ("interested", "not_eligible"))
    holding = [r for r in people if r.get("state") not in ("no_show", "not_eligible")]
    capacity = sum(int(s.get("capacity") or 0) for s in slots) or int(event.get("capacity") or 0)
    return {
        "event": {"title": event.get("title", ""), "date": event.get("event_date", ""), "venue": event.get("venue", ""), "capacity": capacity},
        "registered": len(people), "interested": status["interested"], "confirmed": status["confirmed"],
        "attended": len(attended), "no_show": status["no_show"], "not_eligible": status["not_eligible"],
        "walk_ins": sum(1 for r in people if r.get("source") in ("walkin", "kiosk")),
        "show_rate": _pct(len(attended), booked),
        "fill_rate": _pct(len(holding), capacity or 1),
        "slots": [{"time": s.get("starts_at"), "capacity": int(s.get("capacity") or 0),
                   "booked": sum(1 for r in holding if r.get("slot_id") == s["_key"])}
                  for s in sorted(slots, key=lambda s: s.get("starts_at", ""))],
        "messages": dict(Counter(n.get("channel") for n in notes)),
        "tasks": dict(Counter(t.get("state") or "todo" for t in tasks)),
    }
