# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CALENDAR - pending and approved leave between two dates (everyone, or the people of one site)."""
from grepx_service import RequestContext

from domain import overlaps
from dto import EMPLOYEES, LeaveState
from .common import leaves, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    first, last, site = ctx.text("first"), ctx.text("last") or ctx.text("first"), ctx.text("site_id")
    at_site = {e["_key"] for e in ctx.read.accepted(EMPLOYEES, tenant_id=t) if site in (e.get("sites") or [])} if site else None
    rows = [l for l in leaves(ctx, t) if l["state"] in (LeaveState.PENDING.value, LeaveState.APPROVED.value)
            and overlaps(first, last, l["first"], l["last"]) and (at_site is None or l["employee_id"] in at_site)]
    ctx.accept({"leaves": sorted(rows, key=lambda l: (l["first"], l["name"]))})
