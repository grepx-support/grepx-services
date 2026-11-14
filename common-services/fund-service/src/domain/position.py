# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The position of a set of funds (one fund, or every fund in one currency): totals, real spending per use, pending
promises with their due dates, the forecast and the suggestions. Pure: the caller reads rows and supplies spending."""
from __future__ import annotations

from datetime import date, timedelta

from .advice import suggestions
from .forecast import forecast
from .projection import ebitda_curve
from .spending import linked
from .totals import overdue, totals, uses

SUMMED = ("committed", "received", "pending", "allocated", "spent", "returned", "costs", "available", "interest", "owed")


def summed(funds: list[dict], entries: list[dict]) -> dict:
    out = {k: 0 for k in SUMMED}
    for f in funds:
        t = totals([e for e in entries if e["fund_id"] == f["fund_id"]], f.get("kind") == "loan")
        for k in SUMMED:
            out[k] += t[k]
    return out


def promises(entries: list[dict], names: dict[str, str], today: str) -> list[dict]:
    """Every promise not fully paid: who, how much is missing, due when, overdue or not (oldest first)."""
    return [{**o, "name": names.get(o["party_id"], "?"), "overdue": o["due"] < today} for o in overdue(entries, "9999-12-31")]


def position(funds: list[dict], entries: list[dict], names: dict[str, str], spending: dict, today: str, against: list[dict] | None = None) -> dict:
    tot = summed(funds, entries)
    links = linked(uses(entries), entries, spending or {})
    pending = promises(entries, names, today)
    loans = [{"fund_id": f["fund_id"], "name": f["name"], "rate_pct": f.get("rate_pct", 0),
              "owed": totals([e for e in entries if e["fund_id"] == f["fund_id"]], True)["owed"]} for f in funds if f.get("kind") == "loan"]
    plans = [ebitda_curve(f["plan"]) for f in funds if (f.get("plan") or {}).get("uses")]
    plan_in = [sum(c[i] for c in plans if i < len(c)) * 100 for i in range(12)]          # plan amounts are major units
    burn = sum(u["burn"] for u in links)
    fc = forecast(tot["available"], pending, burn, loans, plan_in, today[:7])
    first_in = min((e["date"] for e in entries if e["kind"] == "receive" and not e.get("reversed")), default=today)
    tips = suggestions({"overdue": [p for p in pending if p["overdue"]], "forecast": fc, "pending": tot["pending"], "available": tot["available"],
                        "linked": links, "loans": loans, "against_plan": against or [],
                        "received_long_ago": first_in <= (date.fromisoformat(today) - timedelta(days=60)).isoformat()})
    return {"totals": tot, "linked": links, "promises": pending, "forecast": fc, "suggestions": tips}
