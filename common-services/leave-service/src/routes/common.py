# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Shared by the routes: the business guard, its leave types (its own, or the defaults), employees, leaves."""
from __future__ import annotations

from grepx_service import RequestContext

from domain import DEFAULTS
from dto import EMPLOYEES, LEAVES, TYPES, ReasonCode


def tenant(ctx: RequestContext) -> str | None:
    t = ctx.text("tenant_id")
    if not t:
        ctx.reject(ReasonCode.MISSING_TENANT)
        return None
    return t


def plain(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_") and k != "status"}


def types(ctx: RequestContext, t: str) -> dict[str, dict]:
    own = {r["type_id"]: plain(r) for r in ctx.read.accepted(TYPES, tenant_id=t)}
    return {**{d["type_id"]: {**d, "active": True} for d in DEFAULTS}, **own}


def employee(ctx: RequestContext, t: str, employee_id: str) -> dict | None:
    row = ctx.read.accepted_one(EMPLOYEES, employee_id) if employee_id else None
    return row if row and row.get("tenant_id") == t else None


def leaves(ctx: RequestContext, t: str, **equals) -> list[dict]:
    return [{**plain(r), "leave_id": r["_key"]} for r in ctx.read.accepted(LEAVES, tenant_id=t, **equals)]
