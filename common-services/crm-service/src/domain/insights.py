# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What the pipeline says: open value and weighted value by stage, deals going stale, the forecast by expected-close
month, win rate, average days from created to won, results by owner and by source, why deals were lost. Pure."""
from __future__ import annotations

from collections import Counter
from datetime import date


def days_between(a: str, b: str) -> int:
    try:
        return (date.fromisoformat(b[:10]) - date.fromisoformat(a[:10])).days
    except (ValueError, TypeError):
        return 0


def board(stages: list[dict], deals: list[dict], last_touch: dict[str, str], today: str) -> list[dict]:
    """Each stage with its open deals (in order, each flagged stale when untouched for the stage's stale_days)."""
    out = []
    for s in stages:
        here = sorted((d for d in deals if d.get("state") == "open" and d["stage"] == s["stage_id"]), key=lambda d: d.get("order", 0))
        here = [{**d, "idle_days": days_between(last_touch.get(d["deal_id"]) or d.get("created_at", today), today)} for d in here]
        here = [{**d, "stale": d["idle_days"] >= s["stale_days"]} for d in here]
        total = sum(d["value"] for d in here)
        out.append({**s, "deals": here, "count": len(here), "value": total, "weighted": round(total * s["chance"] / 100)})
    return out


def _group(deals: list[dict], key: str) -> list[dict]:
    out: dict[str, dict] = {}
    for d in deals:
        g = out.setdefault(d.get(key) or "-", {"name": d.get(key) or "-", "open": 0, "won": 0, "lost": 0, "won_value": 0})
        g[d.get("state", "open")] += 1
        if d.get("state") == "won":
            g["won_value"] += d["value"]
    return sorted(out.values(), key=lambda g: -g["won_value"])


def insights(stages: list[dict], deals: list[dict]) -> dict:
    chance = {s["stage_id"]: s["chance"] for s in stages}
    open_ = [d for d in deals if d.get("state") == "open"]
    won, lost = [d for d in deals if d.get("state") == "won"], [d for d in deals if d.get("state") == "lost"]
    forecast: dict[str, dict] = {}
    for d in open_:
        m = (d.get("expected_close") or "")[:7] or "no date"
        f = forecast.setdefault(m, {"month": m, "value": 0, "weighted": 0, "count": 0})
        f["value"] += d["value"]
        f["weighted"] += round(d["value"] * chance.get(d["stage"], 0) / 100)
        f["count"] += 1
    cycle = [days_between(d.get("created_at", ""), d.get("closed_on", "")) for d in won]
    return {"open": {"count": len(open_), "value": sum(d["value"] for d in open_)},
            "won": {"count": len(won), "value": sum(d["value"] for d in won)}, "lost": {"count": len(lost), "value": sum(d["value"] for d in lost)},
            "win_rate": round(100 * len(won) / (len(won) + len(lost)), 1) if won or lost else None,
            "avg_days_to_win": round(sum(cycle) / len(cycle), 1) if cycle else None,
            "forecast": sorted(forecast.values(), key=lambda f: f["month"]), "by_owner": _group(deals, "owner_name"), "by_source": _group(deals, "source"),
            "lost_reasons": [{"reason": r, "count": n} for r, n in Counter(d.get("lost_reason") or "-" for d in lost).most_common(10)]}
