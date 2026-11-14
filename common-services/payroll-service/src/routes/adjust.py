# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ADJUST - a bonus (added to pay), an advance being recovered or another deduction (taken off) for one person and
month. REMOVE_ADJUSTMENT takes one back. Not once the month is final."""
from grepx_service import RequestContext, new_key

from dto import ADJUSTMENTS, EMPLOYEES, ReasonCode
from .common import month_of, tenant
from .run import final

KINDS = ("bonus", "advance", "deduction")


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    month = t and month_of(ctx)
    if not month:
        return
    emp = ctx.read.accepted_one(EMPLOYEES, ctx.text("employee_id"))
    if emp is None or emp.get("tenant_id") != t:
        return ctx.reject(ReasonCode.UNKNOWN_EMPLOYEE)
    if final(ctx, t, month):
        return ctx.reject(ReasonCode.ALREADY_FINAL)
    try:
        amount = round(float(ctx.get("amount")), 2)
    except (TypeError, ValueError):
        return ctx.reject(ReasonCode.INVALID_AMOUNT)
    if amount <= 0 or ctx.text("kind") not in KINDS:
        return ctx.reject(ReasonCode.INVALID_AMOUNT)
    row = {"tenant_id": t, "month": month, "employee_id": emp["_key"], "kind": ctx.text("kind"), "amount": amount,
           "note": " ".join(ctx.text("note").split())[:80]}
    key = new_key()[:12]
    ctx.emitter.submit(ADJUSTMENTS, key, "ACCEPTED", row)
    ctx.accept({"adjustment": {**row, "adjustment_id": key}})


def remove(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    row = ctx.read.accepted_one(ADJUSTMENTS, ctx.text("adjustment_id"))
    if row is None or row.get("tenant_id") != t:
        return ctx.reject(ReasonCode.INVALID_AMOUNT)
    if final(ctx, t, row["month"]):
        return ctx.reject(ReasonCode.ALREADY_FINAL)
    ctx.emitter.submit(ADJUSTMENTS, row["_key"], "DELETED", {"tenant_id": t})
    ctx.accept({"removed": row["_key"]})
