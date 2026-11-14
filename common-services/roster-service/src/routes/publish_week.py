# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""PUBLISH_WEEK - the week's shifts at a site become visible to staff (and can be sent to them)."""
from datetime import timedelta

from grepx_service import RequestContext

from domain import week_of
from dto import SHIFTS, ReasonCode
from .common import shifts_between, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    try:
        monday, _ = week_of(ctx.text("week"))
    except ValueError:
        return ctx.reject(ReasonCode.INVALID_DATE)
    count = 0
    for s in shifts_between(ctx, t, monday, monday + timedelta(days=6), site_id=ctx.text("site_id")):
        if not s.get("published"):
            ctx.emitter.submit(SHIFTS, s["shift_id"], "ACCEPTED", {**s, "published": True})
            count += 1
    ctx.accept({"published": count})
