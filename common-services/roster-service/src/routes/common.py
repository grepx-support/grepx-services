# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Shared by the routes: the business (tenant) guard, a week's shifts, the employee records (read from employee-service)."""
from __future__ import annotations

from datetime import date, timedelta

from grepx_service import RequestContext

from dto import EMPLOYEES, LEAVES, SHIFTS, ReasonCode


def tenant(ctx: RequestContext) -> str | None:
    t = ctx.text("tenant_id")
    if not t:
        ctx.reject(ReasonCode.MISSING_TENANT)
        return None
    return t


def plain(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_") and k != "status"}


def shifts_between(ctx: RequestContext, t: str, first: date, last: date, **equals) -> list[dict]:
    a, b = first.isoformat(), last.isoformat()
    return [plain(s) for s in ctx.read.accepted(SHIFTS, tenant_id=t, **equals) if a <= s.get("date", "") <= b]


def around(ctx: RequestContext, t: str, day: str, **equals) -> list[dict]:
    """Shifts the day before, on, and after (a night shift can reach into the next day)."""
    d = date.fromisoformat(day)
    return shifts_between(ctx, t, d - timedelta(days=1), d + timedelta(days=1), **equals)


def employee(ctx: RequestContext, t: str, employee_id: str) -> dict | None:
    row = ctx.read.accepted_one(EMPLOYEES, employee_id) if employee_id else None
    return row if row and row.get("tenant_id") == t else None


def employees(ctx: RequestContext, t: str) -> dict[str, dict]:
    return {e["_key"]: e for e in ctx.read.accepted(EMPLOYEES, tenant_id=t)}


def on_leave(ctx: RequestContext, t: str, employee_id: str, day: str) -> dict | None:
    """Approved leave of the person covering the day (leave-service)."""
    for leave in ctx.read.accepted(LEAVES, tenant_id=t, employee_id=employee_id):
        if leave.get("state") == "approved" and leave.get("first", "") <= day <= leave.get("last", ""):
            return leave
    return None


def leaves_between(ctx: RequestContext, t: str, first: str, last: str) -> list[dict]:
    return [plain(l) for l in ctx.read.accepted(LEAVES, tenant_id=t) if l.get("state") in ("approved", "pending")
            and l.get("first", "") <= last and first <= l.get("last", "")]
