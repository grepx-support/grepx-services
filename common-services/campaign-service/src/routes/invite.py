# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""INVITE — personal invitations to filtered people (or an explicit list), skipping those already booked."""
from grepx_service import RequestContext, local_today

from domain import matches_filters
from dto import EVENTS_TABLE, BOOKINGS_TABLE, UNKNOWN_EVENT
from .common import Audience, event_values, send_all


def handle(ctx: RequestContext) -> None:
    event = ctx.read.accepted_one(EVENTS_TABLE, ctx.text("event_id"))
    if event is None:
        return ctx.reject(UNKNOWN_EVENT)
    a = Audience(ctx)
    filters = dict(ctx.get("filters", {}))
    if filters.get("exclude_registered", True):
        filters["exclude"] = [r.get("person_id") for r in ctx.read.accepted(BOOKINGS_TABLE, event_id=event["_key"]) if r.get("state") != "cancelled"]
    only = set(ctx.get("person_ids", []))
    recipients = [p for p in a.people if (not only or p["_key"] in only) and matches_filters(p, a.stats.get(p["_key"], {}), filters, local_today(), a.product)]
    if ctx.get("preview", False):
        return ctx.accept({"count": len(recipients), "names": [d.get("name") for d in recipients[:50]]})
    send_all(ctx, "event_invitation", recipients, event_values(ctx.cfg, event), auto=False)
