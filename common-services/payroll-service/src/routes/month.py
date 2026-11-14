# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""MONTH - the month's run (if any), its payslips (or one person's) and the adjustments entered for it."""
from grepx_service import RequestContext

from dto import RUNS, SLIPS
from .common import adjustments, month_of, plain, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    month = t and month_of(ctx)
    if not month:
        return
    eid = ctx.text("employee_id")
    run = ctx.read.accepted_one(RUNS, f"{t}:{month}")
    slips = [plain(s) for s in ctx.read.accepted(SLIPS, tenant_id=t, month=month) if not eid or s.get("employee_id") == eid]
    ctx.accept({"run": plain(run) if run else None, "payslips": sorted(slips, key=lambda s: s["name"].lower()),
                "adjustments": [a for a in adjustments(ctx, t, month) if not eid or a["employee_id"] == eid]})
