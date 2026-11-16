# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for site-service: one page per business (keyed by its id), replaced whole on each save."""
from grepx_service import ActionDispatcher, RequestContext, now_iso

from domain import clean_page
from dto import PAGES, ReasonCode, SiteAction


def save(ctx: RequestContext) -> None:
    business = ctx.text("business_id")
    if not business:
        return ctx.reject(ReasonCode.MISSING_BUSINESS)
    try:
        page = clean_page(ctx.get("page") or {})
    except ValueError as exc:
        return ctx.reject(str(exc))
    row = {"business_id": business, **page, "updated_at": now_iso(), "updated_by": ctx.text("actor_id")}
    ctx.emitter.submit(PAGES, business, "ACCEPTED", row)
    ctx.accept({"page": row})


handle = ActionDispatcher({SiteAction.SAVE: save}, SiteAction, "site_requests")
