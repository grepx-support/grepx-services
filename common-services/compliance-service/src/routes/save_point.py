# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_POINT - add or change a check at a site (same point_id = change it)."""
from grepx_service import RequestContext, new_key

from domain import clean_point
from dto import POINTS, ReasonCode
from .common import point, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    pid, site = ctx.text("point_id"), ctx.text("site_id")
    if pid and point(ctx, t, pid) is None:
        return ctx.reject(ReasonCode.UNKNOWN_POINT)
    if not site:
        return ctx.reject(ReasonCode.MISSING_SITE)
    try:
        row = clean_point(ctx.fields)
    except ValueError as exc:
        return ctx.reject(str(exc))
    pid = pid or new_key()[:12]
    full = {**row, "site_id": site, "tenant_id": t, "active": True}
    ctx.emitter.submit(POINTS, pid, "ACCEPTED", full)
    ctx.accept({"point": {**full, "point_id": pid}})


def remove(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    p = point(ctx, t, ctx.text("point_id"))
    if p is None:
        return ctx.reject(ReasonCode.UNKNOWN_POINT)
    ctx.emitter.submit(POINTS, p["point_id"], "ACCEPTED", {**{k: v for k, v in p.items() if k != "point_id"}, "active": False})
    ctx.accept({"removed": p["point_id"]})
