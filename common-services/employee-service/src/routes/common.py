# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Shared by the routes: every employee belongs to one business (tenant_id); another business's rows are not there."""
from __future__ import annotations

from grepx_service import RequestContext

from dto import EMPLOYEES, ReasonCode


def tenant(ctx: RequestContext) -> str | None:
    t = ctx.text("tenant_id")
    if not t:
        ctx.reject(ReasonCode.MISSING_TENANT)
        return None
    return t


def mine(ctx: RequestContext, employee_id: str, t: str) -> dict | None:
    row = ctx.read.accepted_one(EMPLOYEES, employee_id) if employee_id else None
    return row if row and row.get("tenant_id") == t else None


def plain(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_") and k != "status"}


def store(ctx: RequestContext, employee_id: str, t: str, row: dict) -> dict:
    full = {**row, "employee_id": employee_id, "tenant_id": t}
    ctx.emitter.submit(EMPLOYEES, employee_id, "ACCEPTED", full)
    return full
