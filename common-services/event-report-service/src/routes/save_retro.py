# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_RETRO — what went well, what to improve, actions (one per line), notes, rating 1–5."""
from grepx_service import RequestContext

from dto import EVENTS_TABLE, INVALID_RATING, REPORTS_TABLE, RETRO_FIELDS, UNKNOWN_EVENT
from .common import compute, save


def handle(ctx: RequestContext) -> None:
    event = ctx.read.accepted_one(EVENTS_TABLE, ctx.text("event_id"))
    if event is None:
        return ctx.reject(UNKNOWN_EVENT)
    rating = int(ctx.get("rating", 0) or 0)
    if not 0 <= rating <= 5:
        return ctx.reject(INVALID_RATING)
    old = ctx.read.accepted_one(REPORTS_TABLE, event["_key"]) or {}
    retro = {k: (ctx.get(k) if k in ctx.fields else old.get(k, "")) for k in RETRO_FIELDS}
    save(ctx, event["_key"], {**retro, "rating": rating, "updated_by": ctx.text("actor_id"), "title": event.get("title", ""),
                              "stats": old.get("stats") or compute(ctx, event)})
