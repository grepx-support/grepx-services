# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""LOG_ACTIVITY (a note, call, email, meeting, WhatsApp, or a task to do) and COMPLETE_ACTIVITY (with an outcome)."""
from grepx_service import RequestContext

from domain import clean_activity
from dto import ACTIVITIES, CONTACTS, DEALS
from .common import mine, now_iso, plain, run, save


def log(ctx: RequestContext) -> None:
    def body(t):
        row = clean_activity({k: ctx.get(k) for k in ("kind", "subject", "body", "contact_id", "deal_id", "due", "owner_id", "owner_name", "outcome")}, now_iso())
        if row["contact_id"] and mine(ctx, CONTACTS, row["contact_id"], t) is None:
            raise ValueError("UNKNOWN_CONTACT")
        deal = mine(ctx, DEALS, row["deal_id"], t) if row["deal_id"] else None
        if row["deal_id"] and deal is None:
            raise ValueError("UNKNOWN_DEAL")
        if deal and not row["contact_id"]:
            row["contact_id"] = deal.get("contact_id", "")
        return {"activity": save(ctx, ACTIVITIES, None, {**row, "tenant_id": t}, "activity_id")}
    run(ctx, body)


def complete(ctx: RequestContext) -> None:
    def body(t):
        row = mine(ctx, ACTIVITIES, ctx.text("activity_id"), t)
        if row is None:
            raise ValueError("UNKNOWN_ACTIVITY")
        done = {**plain(row, "activity_id"), "done": ctx.get("done") is not False, "done_at": now_iso(), "outcome": ctx.text("outcome")[:80]}
        return {"activity": save(ctx, ACTIVITIES, done["activity_id"], done, "activity_id")}
    run(ctx, body)
