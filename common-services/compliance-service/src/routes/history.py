# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""HISTORY - every record between two dates (a site's, or all), newest first, with the totals inspectors ask for."""
from grepx_service import RequestContext

from dto import LOGS
from .common import plain, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    first, last, site = ctx.text("first"), ctx.text("last"), ctx.text("site_id")
    rows = [{**plain(l), "log_id": l["_key"]} for l in ctx.read.accepted(LOGS, tenant_id=t, **({"site_id": site} if site else {}))
            if first <= l.get("date", "") <= last]
    rows.sort(key=lambda l: l["at"], reverse=True)
    ctx.accept({"records": rows[:2000], "total": len(rows), "failed": sum(1 for r in rows if not r["ok"])})
