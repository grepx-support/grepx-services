# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""REQUEST - ask for leave. Refused when it overlaps the person's other leave, or takes more than is left of a limited
type this year. Weekly days off (default Sunday; days_off=[5,6] for Saturday and Sunday) are not counted."""
from grepx_service import RequestContext, new_key, now_iso

from domain import balance, leave_days, overlaps, parse
from dto import LEAVES, LeaveState, ReasonCode
from .common import employee, leaves, tenant, types

LIVE = (LeaveState.PENDING.value, LeaveState.APPROVED.value)


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    eid = ctx.text("employee_id")
    emp = employee(ctx, t, eid)
    if emp is None:
        return ctx.reject(ReasonCode.UNKNOWN_EMPLOYEE)
    kind = types(ctx, t).get(ctx.text("type_id"))
    if kind is None or not kind.get("active", True):
        return ctx.reject(ReasonCode.UNKNOWN_TYPE)
    try:
        first, last = parse(ctx.text("first")), parse(ctx.text("last") or ctx.text("first"))
        days = leave_days(first, last, bool(ctx.get("half_day")), tuple(ctx.get("days_off") or (6,)))
    except ValueError as exc:
        return ctx.reject(str(exc))
    mine = leaves(ctx, t, employee_id=eid)
    if any(l["state"] in LIVE and overlaps(first.isoformat(), last.isoformat(), l["first"], l["last"]) for l in mine):
        return ctx.reject(ReasonCode.OVERLAPS)
    left = balance(kind, mine, first.year, emp.get("start_date", ""))["left"]
    if not kind.get("unlimited") and days > left:
        return ctx.reject(ReasonCode.NOT_ENOUGH_BALANCE, f"{left:g} left")
    row = {"tenant_id": t, "employee_id": eid, "name": emp.get("name", ""), "type_id": kind["type_id"], "type_name": kind["name"],
           "paid": kind.get("paid", True), "first": first.isoformat(), "last": last.isoformat(), "days": days, "half_day": bool(ctx.get("half_day")),
           "note": str(ctx.get("note") or "")[:300], "state": LeaveState.PENDING.value, "asked_at": now_iso(), "asked_by": ctx.text("actor_name")}
    leave_id = new_key()[:12]
    ctx.emitter.submit(LEAVES, leave_id, "ACCEPTED", row)
    ctx.accept({"leave": {**row, "leave_id": leave_id}})
