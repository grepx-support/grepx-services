# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ANNOUNCE — tell an audience about a new event (automatic message: admins control wording/channels)."""
from grepx_service import RequestContext, local_today

from domain import AudienceError, resolve_audience
from dto import EVENTS_TABLE, UNKNOWN_EVENT
from .common import Audience, event_values, send_all


def handle(ctx: RequestContext) -> None:
    event = ctx.read.accepted_one(EVENTS_TABLE, ctx.text("event_id"))
    if event is None:
        return ctx.reject(UNKNOWN_EVENT)
    a = Audience(ctx)
    try:
        recipients = resolve_audience(ctx.text("audience") or a.member, a.people, a.stats, a.roles, local_today(), a.member, a.product)
    except AudienceError as exc:
        return ctx.reject(str(exc))
    send_all(ctx, "event_announcement", recipients, event_values(ctx.cfg, event), auto=True)
