# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Suggestions: plain rules over the position, each a small function (Chain of Responsibility: every rule looks, any
may speak). A suggestion: code, level (act / watch / idea), title, why, and what it is about (fund / party / use)."""
from __future__ import annotations

RUNWAY_SHORT, IDLE_MONTHS, HIGH_RATE, IDLE_DAYS = 6, 6, 8.0, 60


def chase(p) -> list[dict]:
    return [{"code": "CHASE_PROMISE", "level": "act", "title": f"Chase {o['name']}", "why": f"Promised money was due on {o['due']} and is not all in.",
             "amount": o["missing"], "party_id": o["party_id"], "fund_id": o.get("fund_id", "")} for o in p["overdue"]]


def runway(p) -> list[dict]:
    left = p["forecast"]["runway"]["expected"]
    if left is None or left >= RUNWAY_SHORT:
        return []
    return [{"code": "RUNWAY_SHORT", "level": "act", "title": f"Cash runs out in about {left} month{'s' if left != 1 else ''}",
             "why": "At today's spending the money available and promised does not last. Collect what is pending or raise more.", "amount": p["pending"]}]


def overspent(p) -> list[dict]:
    return [{"code": "USE_OVERSPENT", "level": "act", "title": f"{u['purpose']} has spent more than it was given", "amount": u["spent"] - u["allocated"],
             "why": "Put more money to this use, or bring its costs down.", "purpose": u["purpose"]} for u in p["linked"] if u["over"]]


def idle(p) -> list[dict]:
    burn = p["forecast"]["burn"]
    if not p["available"] or (burn and p["available"] < burn * IDLE_MONTHS) or (not burn and not p["received_long_ago"]):
        return []
    return [{"code": "CASH_IDLE", "level": "idea", "title": "Money is sitting idle", "amount": p["available"],
             "why": f"It covers more than {IDLE_MONTHS} months of spending. Put it to use, or pay back a loan."}]


def repay(p) -> list[dict]:
    return [{"code": "REPAY_LOAN", "level": "idea", "title": f"Consider paying {l['name']} back early", "amount": min(l["owed"], p["available"]),
             "why": f"It charges {l['rate_pct']}% a year; the fund has money available.", "fund_id": l["fund_id"]}
            for l in p["loans"] if float(l.get("rate_pct") or 0) >= HIGH_RATE and l["owed"] > 0 and p["available"] >= l["owed"] * 0.25]


def behind_plan(p) -> list[dict]:
    return [{"code": "BEHIND_PLAN", "level": "watch", "title": f"{a['purpose']} earns less than planned", "purpose": a["purpose"],
             "why": f"Its recent months are at {a['pct_of_plan']}% of the plan.", "amount": 0} for a in p["against_plan"] if a.get("pct_of_plan") is not None and a["pct_of_plan"] < 80]


RULES = (chase, runway, overspent, behind_plan, repay, idle)
ORDER = {"act": 0, "watch": 1, "idea": 2}


def suggestions(position: dict) -> list[dict]:
    """position: overdue, forecast, pending, available, linked, loans, against_plan, received_long_ago."""
    return sorted((s for rule in RULES for s in rule(position)), key=lambda s: ORDER[s["level"]])
