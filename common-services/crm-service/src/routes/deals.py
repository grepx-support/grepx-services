# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_DEAL, MOVE_DEAL (drag to a stage and place), CLOSE_DEAL (won / lost with why), REOPEN_DEAL."""
from grepx_service import RequestContext

from domain import clean_deal, close, move, reopen
from dto import CONTACTS, DEALS
from .common import deals, mine, now_iso, plain, run, save, stages, today


def _deal(ctx, t) -> dict:
    row = mine(ctx, DEALS, ctx.text("deal_id"), t)
    if row is None:
        raise ValueError("UNKNOWN_DEAL")
    return plain(row, "deal_id")


def save_deal(ctx: RequestContext) -> None:
    def body(t):
        key = ctx.text("deal_id")
        cur = _deal(ctx, t) if key else None
        for c in (ctx.text("contact_id"), ctx.text("company_id")):
            if c and mine(ctx, CONTACTS, c, t) is None:
                raise ValueError("UNKNOWN_CONTACT")
        fields = {k: ctx.get(k) for k in ("title", "stage", "value", "currency", "contact_id", "company_id", "owner_id", "owner_name",
                                          "source", "notes", "expected_close", "goods") if ctx.get(k) is not None}
        row = {**clean_deal(fields, stages(ctx, t), cur), "tenant_id": t, "created_at": (cur or {}).get("created_at") or today(ctx)}
        if cur is None:
            row["order"] = len([d for d in deals(ctx, t, stage=row["stage"]) if d.get("state") == "open"])
        return {"deal": save(ctx, DEALS, key or None, row, "deal_id")}
    run(ctx, body)


def move_deal(ctx: RequestContext) -> None:
    def body(t):
        deal = _deal(ctx, t)
        stage = ctx.text("stage") or deal["stage"]
        if stage not in {s["stage_id"] for s in stages(ctx, t)}:
            raise ValueError("INVALID_STAGE")
        if deal.get("state") != "open":
            raise ValueError("DEAL_CLOSED")
        column = move(deals(ctx, t), deal["deal_id"], stage, int(ctx.get("index") or 0))
        for d in column:
            save(ctx, DEALS, d["deal_id"], {**d, "moved_at": now_iso()} if d["deal_id"] == deal["deal_id"] else d, "deal_id")
        return {"deal": next(d for d in column if d["deal_id"] == deal["deal_id"]), "column": [d["deal_id"] for d in column]}
    run(ctx, body)


def close_deal(ctx: RequestContext) -> None:
    def body(t):
        out = close(_deal(ctx, t), bool(ctx.get("won")), ctx.text("reason"), today(ctx))
        return {"deal": save(ctx, DEALS, out["deal_id"], out, "deal_id")}
    run(ctx, body)


def reopen_deal(ctx: RequestContext) -> None:
    def body(t):
        out = reopen(_deal(ctx, t))
        return {"deal": save(ctx, DEALS, out["deal_id"], out, "deal_id")}
    run(ctx, body)
