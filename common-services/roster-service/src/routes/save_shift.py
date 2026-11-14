# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_SHIFT - add or change one shift. Refused when the person already works then (at any site) or is not one of
the business's employees, or is on approved leave that day; an open shift (nobody yet) is fine. A changed shift goes back to draft."""
from grepx_service import RequestContext, new_key

from domain import clashes, clean_shift
from dto import SHIFTS, ReasonCode
from .common import around, employee, on_leave, plain, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    shift_id = ctx.text("shift_id")
    current = ctx.read.accepted_one(SHIFTS, shift_id) if shift_id else None
    if shift_id and (current is None or current.get("tenant_id") != t):
        return ctx.reject(ReasonCode.UNKNOWN_SHIFT)
    raw = {**(plain(current) if current else {}), **{k: v for k, v in ctx.fields.items() if v is not None}}
    try:
        shift = clean_shift(raw)
    except ValueError as exc:
        return ctx.reject(str(exc))
    if shift["employee_id"] and employee(ctx, t, shift["employee_id"]) is None:
        return ctx.reject(ReasonCode.UNKNOWN_EMPLOYEE)
    away = shift["employee_id"] and on_leave(ctx, t, shift["employee_id"], shift["date"])
    if away:
        return ctx.reject(ReasonCode.ON_LEAVE, f"{away.get('type_name', 'leave')} {away['first']} - {away['last']}")
    shift_id = shift_id or new_key()[:12]
    clash = clashes({**shift, "shift_id": shift_id}, around(ctx, t, shift["date"]))
    if clash:
        return ctx.reject(ReasonCode.DOUBLE_BOOKED, f"{clash[0]['date']} {clash[0]['start']}-{clash[0]['end']}")
    full = {**shift, "shift_id": shift_id, "tenant_id": t, "published": False}
    ctx.emitter.submit(SHIFTS, shift_id, "ACCEPTED", full)
    ctx.accept({"shift": full})
