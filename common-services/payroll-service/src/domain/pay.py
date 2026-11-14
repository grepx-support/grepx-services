# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""One person's pay for one month (Template Method: earnings, then the country's deductions, then the totals).

Monthly salary: the salary for the days employed this month, less unpaid leave (salary / days in month a day).
Hourly: hours worked (clock-ins) x rate. Overtime: hours worked past the contracted weekly hours x weeks in the month,
paid at the overtime multiple. Bonuses add; advances and other deductions come off the net."""
from __future__ import annotations

import calendar
from datetime import date

from .countries import COUNTRIES

WEEKS_PER_MONTH = 52 / 12


def employed_days(employee: dict, month: str) -> tuple[int, int]:
    y, m = int(month[:4]), int(month[5:7])
    total = calendar.monthrange(y, m)[1]
    first, last = date(y, m, 1), date(y, m, total)
    start = max(first, date.fromisoformat(employee["start_date"])) if employee.get("start_date") else first
    end = min(last, date.fromisoformat(employee["end_date"])) if employee.get("end_date") else last
    return max(0, (end - start).days + 1), total


def earnings(employee: dict, month: str, worked_min: int, unpaid_days: float, s: dict) -> list[dict]:
    pay = employee.get("pay") or {}
    rate, weekly = float(pay.get("rate") or 0), float(pay.get("weekly_hours") or 0)
    worked = worked_min / 60
    days, total = employed_days(employee, month)
    out = []
    if pay.get("basis") == "hourly":
        out.append({"code": "hours", "label": f"{worked:.1f} hours x {rate:g}", "amount": worked * rate})
        hour_rate, extra = rate, s["overtime_multiplier"] - 1
    else:
        out.append({"code": "salary", "label": "Salary" + (f" ({days} of {total} days)" if days < total else ""), "amount": rate * days / total})
        if unpaid_days:
            out.append({"code": "unpaid", "label": f"Unpaid leave ({unpaid_days:g} days)", "amount": -rate / total * unpaid_days})
        hour_rate, extra = (rate / (weekly * WEEKS_PER_MONTH) if weekly else 0.0), s["overtime_multiplier"]
    overtime = max(0.0, worked - weekly * WEEKS_PER_MONTH * days / total) if weekly and worked_min else 0.0
    if overtime and hour_rate:
        out.append({"code": "overtime", "label": f"Overtime {overtime:.1f} h x {s['overtime_multiplier']:g}", "amount": overtime * hour_rate * extra})
    return [{**e, "amount": round(e["amount"], 2)} for e in out if round(e["amount"], 2)]


def payslip(employee: dict, month: str, worked_min: int, unpaid_days: float, adjustments: list[dict], settings: dict) -> dict:
    s = settings["rates"]
    lines = earnings(employee, month, worked_min, unpaid_days, s)
    lines += [{"code": a["kind"], "label": a.get("note") or a["kind"].capitalize(), "amount": round(float(a["amount"]), 2)}
              for a in adjustments if a["kind"] == "bonus"]
    gross = round(sum(l["amount"] for l in lines), 2)
    basic = round(sum(l["amount"] for l in lines if l["code"] in ("salary", "unpaid", "hours")) * s.get("basic_pct", 100) / 100, 2)
    statutory = COUNTRIES[settings["country"]].deductions({"gross": gross, "basic": basic, "monthly_equivalent": gross}, s)
    taken = [l for l in statutory if not l["employer"]] + [{"code": a["kind"], "label": a.get("note") or a["kind"].capitalize(),
                                                           "amount": round(float(a["amount"]), 2), "employer": False}
                                                          for a in adjustments if a["kind"] != "bonus"]
    employer = [l for l in statutory if l["employer"]]
    net = round(gross - sum(l["amount"] for l in taken), 2)
    return {"employee_id": employee["_key"], "name": employee.get("name", ""), "position": employee.get("position", ""),
            "site_id": employee.get("home_site", ""), "month": month, "earnings": lines, "gross": gross, "basic": basic,
            "deductions": taken, "employer": employer, "net": net, "cost": round(gross + sum(l["amount"] for l in employer), 2),
            "worked_hours": round(worked_min / 60, 1), "unpaid_days": unpaid_days}
