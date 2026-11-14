# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""FINALISE - lock the month's run: its payslips no longer change and can be sent. Returns the cost per site."""
from grepx_service import RequestContext, now_iso

from dto import RUNS, SLIPS, ReasonCode
from .common import month_of, plain, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    month = t and month_of(ctx)
    if not month:
        return
    run = ctx.read.accepted_one(RUNS, f"{t}:{month}")
    if run is None:
        return ctx.reject(ReasonCode.NO_RUN)
    if run.get("final"):
        return ctx.reject(ReasonCode.ALREADY_FINAL)
    done = {**plain(run), "final": True, "finalised_at": now_iso(), "finalised_by": ctx.text("actor_name")}
    ctx.emitter.submit(RUNS, run["_key"], "ACCEPTED", done)
    by_site: dict[str, float] = {}
    for slip in ctx.read.accepted(SLIPS, tenant_id=t, month=month):
        by_site[slip.get("site_id", "")] = round(by_site.get(slip.get("site_id", ""), 0) + float(slip.get("cost") or 0), 2)
    ctx.accept({"run": done, "cost_by_site": by_site})
