# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Cash forecast, month by month, in three cases. It starts from the money available. Money comes in as promises fall
due, and in the best case also as the plan's expected earnings. Money goes out as the uses' real monthly burn and as
loan interest.
  expected  promises paid in their due month; burn as now
  best      the same plus the plan's earnings; burn 15 % lower
  worst     overdue promises never come, the rest a month late; burn 15 % higher
Runway: the months until the cash would run out (None when it lasts the whole horizon)."""
from __future__ import annotations

CASES = {"expected": (1.0, 0, False, False), "best": (0.85, 0, True, False), "worst": (1.15, 1, False, True)}   # burn x, months late, plan in, drop overdue


def add_months(month: str, n: int) -> str:
    y, m = int(month[:4]), int(month[5:7]) - 1 + n
    return f"{y + m // 12:04d}-{m % 12 + 1:02d}"


def run(available: int, promises: list[dict], burn: int, interest: int, plan_in: list[float], start: str, horizon: int, case: str) -> dict:
    factor, late, with_plan, drop = CASES[case]
    due: dict[str, int] = {}
    for p in promises:
        if drop and p.get("overdue"):
            continue
        month = max(start, add_months((p.get("due") or start)[:7], late))
        due[month] = due.get(month, 0) + int(p["missing"])
    cash, rows, runway = available, [], None
    for i in range(horizon):
        month = add_months(start, i)
        money_in = due.get(month, 0) + (round(plan_in[i]) if with_plan and i < len(plan_in) else 0)
        money_out = round(burn * factor) + interest
        opening, cash = cash, cash + money_in - money_out
        rows.append({"month": month, "opening": opening, "in": money_in, "out": money_out, "closing": cash})
        if cash < 0 and runway is None:
            runway = i
    return {"months": rows, "runway": runway}


def forecast(available: int, promises: list[dict], burn: int, loans: list[dict], plan_in: list[float], start: str, horizon: int = 12) -> dict:
    """promises: [{due, missing, overdue}]; loans: [{owed, rate_pct}] (monthly interest = owed x rate / 12)."""
    interest = round(sum(l["owed"] * float(l.get("rate_pct") or 0) / 1200 for l in loans if l["owed"] > 0))
    cases = {c: run(available, promises, burn, interest, plan_in, start, horizon, c) for c in CASES}
    return {"cases": cases, "burn": burn, "interest": interest, "runway": {c: v["runway"] for c, v in cases.items()}}
