# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""WEEK - one site's week (or every site's, when no site is named): the shifts, hours and cost per person, open
shifts, people over the weekly limit, and who clocked in."""
from datetime import timedelta

from grepx_service import RequestContext

from domain import week_of, week_summary
from dto import ATTENDANCE, ReasonCode
from .common import employees, plain, shifts_between, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    try:
        monday, sunday = week_of(ctx.text("week"))
    except ValueError:
        return ctx.reject(ReasonCode.INVALID_DATE)
    site = ctx.text("site_id")
    shifts = shifts_between(ctx, t, monday, sunday, **({"site_id": site} if site else {}))
    a, b = monday.isoformat(), sunday.isoformat()
    worked = [plain(r) for r in ctx.read.accepted(ATTENDANCE, tenant_id=t) if a <= r.get("date", "") <= b
              and (not site or r.get("site_id") == site)]
    ctx.accept({"week": {"monday": a, "site_id": site, "shifts": sorted(shifts, key=lambda s: (s["date"], s["start"])),
                         "summary": week_summary(shifts, employees(ctx, t)), "attendance": worked}})
