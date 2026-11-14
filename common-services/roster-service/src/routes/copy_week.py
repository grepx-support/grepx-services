# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""COPY_WEEK - repeat one week's shifts at a site in another week (same weekday and times). Shifts that would clash
are skipped and counted, so copying twice adds nothing."""
from datetime import date, timedelta

from grepx_service import RequestContext, new_key

from domain import clashes, week_of
from dto import SHIFTS, ReasonCode
from .common import shifts_between, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    site = ctx.text("site_id")
    try:
        src, _ = week_of(ctx.text("from_week"))
        dst, _ = week_of(ctx.text("to_week"))
    except ValueError:
        return ctx.reject(ReasonCode.INVALID_DATE)
    shift_by = dst - src
    have = shifts_between(ctx, t, dst - timedelta(days=1), dst + timedelta(days=7))
    copied = skipped = 0
    for s in shifts_between(ctx, t, src, src + timedelta(days=6), site_id=site):
        new = {**s, "date": (date.fromisoformat(s["date"]) + shift_by).isoformat(), "shift_id": new_key()[:12], "published": False}
        same = any(h["site_id"] == new["site_id"] and h["date"] == new["date"] and h["start"] == new["start"]
                   and h.get("employee_id") == new.get("employee_id") for h in have)
        if same or clashes(new, have):
            skipped += 1
            continue
        ctx.emitter.submit(SHIFTS, new["shift_id"], "ACCEPTED", new)
        have.append(new)
        copied += 1
    ctx.accept({"copied": copied, "skipped": skipped})
