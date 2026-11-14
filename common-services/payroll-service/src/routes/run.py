# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RUN - work out every payslip of the month from the employee records, clock-ins, approved unpaid leave and the
month's adjustments, with the country's rules. Can be run again until FINALISE locks the month."""
from grepx_service import RequestContext, now_iso

from domain import payslip
from dto import RUNS, SLIPS, ReasonCode
from .common import adjustments, month_of, paid_in, settings, tenant, unpaid_days, worked_minutes


def final(ctx: RequestContext, t: str, month: str) -> bool:
    return bool((ctx.read.accepted_one(RUNS, f"{t}:{month}") or {}).get("final"))


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    month = t and month_of(ctx)
    if not month:
        return
    if final(ctx, t, month):
        return ctx.reject(ReasonCode.ALREADY_FINAL)
    s = settings(ctx, t)
    worked, unpaid, extra = worked_minutes(ctx, t, month), unpaid_days(ctx, t, month, s["rates"]["days_off"]), adjustments(ctx, t, month)
    slips = [payslip(e, month, worked.get(e["_key"], 0), unpaid.get(e["_key"], 0), [a for a in extra if a["employee_id"] == e["_key"]], s)
             for e in paid_in(ctx, t, month)]
    for slip in slips:
        ctx.emitter.submit(SLIPS, f"{t}:{month}:{slip['employee_id']}", "ACCEPTED", {**slip, "tenant_id": t})
    totals = {k: round(sum(sl[k] for sl in slips), 2) for k in ("gross", "net", "cost")}
    run = {"tenant_id": t, "month": month, "country": s["country"], "currency": s["currency"], "people": len(slips), **totals,
           "final": False, "worked_out_at": now_iso(), "by": ctx.text("actor_name")}
    ctx.emitter.submit(RUNS, f"{t}:{month}", "ACCEPTED", run)
    ctx.accept({"run": run})
