# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Shared by the routes: the business guard, its settings, a month's inputs (employees, clock-ins, unpaid leave)."""
from __future__ import annotations

import calendar
from datetime import date, timedelta

from grepx_service import RequestContext

from domain import merged
from dto import ADJUSTMENTS, ATTENDANCE, EMPLOYEES, LEAVES, SETTINGS, ReasonCode


def tenant(ctx: RequestContext) -> str | None:
    t = ctx.text("tenant_id")
    if not t:
        ctx.reject(ReasonCode.MISSING_TENANT)
        return None
    return t


def month_of(ctx: RequestContext) -> str | None:
    m = ctx.text("month")
    try:
        date.fromisoformat(f"{m}-01")
        return m
    except ValueError:
        ctx.reject(ReasonCode.INVALID_MONTH)
        return None


def plain(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_") and k != "status"}


def settings(ctx: RequestContext, t: str) -> dict:
    return merged(ctx.read.accepted_one(SETTINGS, t))


def paid_in(ctx: RequestContext, t: str, month: str) -> list[dict]:
    """Employees on the payroll this month (started by its end, not left before its start)."""
    first, last = f"{month}-01", f"{month}-{calendar.monthrange(int(month[:4]), int(month[5:]))[1]:02d}"
    return [e for e in ctx.read.accepted(EMPLOYEES, tenant_id=t) if (e.get("start_date") or "") <= last and (e.get("end_date") or "9999") >= first]


def worked_minutes(ctx: RequestContext, t: str, month: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for a in ctx.read.accepted(ATTENDANCE, tenant_id=t):
        if str(a.get("date", "")).startswith(month):
            out[a["employee_id"]] = out.get(a["employee_id"], 0) + int(a.get("worked_min") or 0)
    return out


def unpaid_days(ctx: RequestContext, t: str, month: str, days_off: list[int]) -> dict[str, float]:
    """Approved unpaid leave days inside the month (weekly days off not counted)."""
    out: dict[str, float] = {}
    for leave in ctx.read.accepted(LEAVES, tenant_id=t, state="approved"):
        if leave.get("paid", True):
            continue
        d, end = date.fromisoformat(leave["first"]), date.fromisoformat(leave["last"])
        while d <= end:
            if d.isoformat().startswith(month) and d.weekday() not in days_off:
                out[leave["employee_id"]] = out.get(leave["employee_id"], 0) + (0.5 if leave.get("half_day") else 1)
            d += timedelta(days=1)
    return out


def adjustments(ctx: RequestContext, t: str, month: str) -> list[dict]:
    return [{**plain(a), "adjustment_id": a["_key"]} for a in ctx.read.accepted(ADJUSTMENTS, tenant_id=t, month=month)]
