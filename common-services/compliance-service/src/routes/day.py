# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""DAY - a site's checks on one day: today's records of each, how many are still due, failures."""
from datetime import date, timedelta

from grepx_service import RequestContext

from domain import due
from dto import LOGS, ReasonCode
from .common import plain, points, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    site = ctx.text("site_id")
    try:
        day = date.fromisoformat(ctx.text("date")) if ctx.text("date") else date.today()
    except ValueError:
        return ctx.reject(ReasonCode.INVALID_DATE)
    week_ago = (day - timedelta(days=6)).isoformat()
    logs = [plain(l) for l in ctx.read.accepted(LOGS, tenant_id=t, **({"site_id": site} if site else {}))
            if week_ago <= l.get("date", "") <= day.isoformat()]
    out = []
    for p in points(ctx, t, site):
        mine = [l for l in logs if l["point_id"] == p["point_id"]]
        today = sorted((l for l in mine if l["date"] == day.isoformat()), key=lambda l: l["at"])
        out.append({**p, "today": today, "due": due(p, len(today), len(mine)), "failed_today": sum(1 for l in today if not l["ok"])})
    ctx.accept({"date": day.isoformat(), "points": sorted(out, key=lambda p: (p.get("group", ""), p["name"])),
                "due": sum(p["due"] for p in out), "failed": sum(p["failed_today"] for p in out)})
