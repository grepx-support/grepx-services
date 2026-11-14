# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Hours and cost of a week's shifts. Pay basis comes from the employee (employee-service): hourly = rate per hour;
monthly = salary spread over the contracted weekly hours (52 weeks / 12 months), so a rostered hour has a cost too.
Strategy pattern: one small class per pay basis."""
from __future__ import annotations

from .times import paid_minutes

WEEKS_PER_MONTH = 52 / 12
MAX_WEEK_MINUTES = 48 * 60       # warn past 48 hours a week (common legal limit)


class Hourly:
    @staticmethod
    def per_hour(pay: dict) -> float:
        return float(pay.get("rate") or 0)


class Monthly:
    @staticmethod
    def per_hour(pay: dict) -> float:
        hours = float(pay.get("weekly_hours") or 0) or 40.0
        return float(pay.get("rate") or 0) / (hours * WEEKS_PER_MONTH)


BASIS = {"hourly": Hourly, "monthly": Monthly}


def hour_cost(employee: dict | None) -> float:
    pay = (employee or {}).get("pay") or {}
    return BASIS.get(pay.get("basis") or "monthly", Monthly).per_hour(pay)


def week_summary(shifts: list[dict], employees: dict[str, dict]) -> dict:
    people, total_min, total_cost = {}, 0, 0.0
    for s in shifts:
        m = paid_minutes(s)
        cost = m / 60 * hour_cost(employees.get(s.get("employee_id")))
        total_min += m
        total_cost += cost
        if s.get("employee_id"):
            p = people.setdefault(s["employee_id"], {"employee_id": s["employee_id"], "minutes": 0, "cost": 0.0, "shifts": 0})
            p["minutes"] += m
            p["cost"] += cost
            p["shifts"] += 1
    for p in people.values():
        p["cost"] = round(p["cost"], 2)
        p["over_limit"] = p["minutes"] > MAX_WEEK_MINUTES
    return {"people": sorted(people.values(), key=lambda p: -p["minutes"]), "minutes": total_min, "cost": round(total_cost, 2),
            "open_shifts": sum(1 for s in shifts if not s.get("employee_id"))}
