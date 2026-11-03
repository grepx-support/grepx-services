# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""BROADCAST — staff message to an audience or a hand-picked list."""
from grepx_service import RequestContext, local_today

from domain import AudienceError, resolve_audience
from dto import MISSING_TEXT
from .common import Audience, send_all


def handle(ctx: RequestContext) -> None:
    if not ctx.text("text"):
        return ctx.reject(MISSING_TEXT)
    a = Audience(ctx)
    only = set(ctx.get("person_ids", []))
    try:
        recipients = ([p for p in a.people if p["_key"] in only] if only else
                      resolve_audience(ctx.text("audience") or a.member, a.people, a.stats, a.roles, local_today(), a.member, a.product))
    except AudienceError as exc:
        return ctx.reject(str(exc))
    send_all(ctx, "broadcast", recipients, {"subject": ctx.text("subject"), "text": ctx.text("text")}, auto=False)
