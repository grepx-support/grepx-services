# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CLOCK - clock in (or out, when already in). Proof: the person's PIN, or verified=true from a client that already
matched the signed-in person to this employee. The shift is found on the roster (late minutes noted); clocking at a
site the person does not work at is refused."""
from datetime import datetime

from grepx_service import RequestContext, new_key

from domain import late_minutes, shift_for, worked_minutes
from dto import ATTENDANCE, PINS, ReasonCode
from .common import around, employee, plain, tenant
from .set_pin import digest


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    eid, site = ctx.text("employee_id"), ctx.text("site_id")
    emp = employee(ctx, t, eid)
    if emp is None:
        return ctx.reject(ReasonCode.UNKNOWN_EMPLOYEE)
    if not ctx.get("verified"):
        saved = ctx.read.accepted_one(PINS, f"{t}:{eid}")
        if saved is None or saved.get("hash") != digest(t, eid, ctx.text("pin")):
            return ctx.reject(ReasonCode.WRONG_PIN)
    if site and site not in (emp.get("sites") or []):
        return ctx.reject(ReasonCode.NOT_AT_THIS_SITE)
    try:
        at = datetime.fromisoformat(ctx.text("at")[:19]) if ctx.text("at") else datetime.now()
    except ValueError:
        return ctx.reject(ReasonCode.INVALID_TIME)
    ctx.accept({"pin": "", **clock(ctx, t, eid, site, at)})


def clock(ctx: RequestContext, t: str, eid: str, site: str, at: datetime) -> dict:
    open_ = [r for r in ctx.read.accepted(ATTENDANCE, tenant_id=t, employee_id=eid) if not r.get("clock_out")]
    if open_:
        row = plain(open_[0])
        row.update(clock_out=at.isoformat(timespec="minutes"), worked_min=worked_minutes(datetime.fromisoformat(row["clock_in"]), at,
                                                                                           row.get("break_min", 0)))
        ctx.emitter.submit(ATTENDANCE, open_[0]["_key"], "ACCEPTED", row)
        return {"clocked": "out", "attendance": row}
    shift = shift_for(around(ctx, t, at.date().isoformat(), employee_id=eid), at)
    row = {"tenant_id": t, "employee_id": eid, "site_id": site or (shift or {}).get("site_id", ""), "date": at.date().isoformat(),
           "clock_in": at.isoformat(timespec="minutes"), "clock_out": "", "shift_id": (shift or {}).get("shift_id", ""),
           "late_min": late_minutes(shift, at), "break_min": (shift or {}).get("break_min", 0), "worked_min": 0}
    ctx.emitter.submit(ATTENDANCE, new_key()[:14], "ACCEPTED", row)
    return {"clocked": "in", "attendance": row}
