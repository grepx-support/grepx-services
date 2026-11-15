# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_PIPELINE and the read views: BOARD, TIMELINE, AGENDA, INSIGHTS."""
from grepx_service import RequestContext

from domain import board, bucket, clean_stages, insights
from dto import CONTACTS, PIPELINES
from .common import activities, contacts, deals, mine, plain, run, stages, today


def save_pipeline(ctx: RequestContext) -> None:
    def body(t):
        rows = clean_stages(ctx.get("stages"))
        ctx.emitter.submit(PIPELINES, t, "ACCEPTED", {"tenant_id": t, "stages": rows})
        return {"stages": rows}
    run(ctx, body)


def _last_touch(acts: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for a in acts:
        if a.get("deal_id") and a.get("done"):
            out[a["deal_id"]] = max(out.get(a["deal_id"], ""), (a.get("done_at") or a["at"])[:10])
    return out


def board_view(ctx: RequestContext) -> None:
    def body(t):
        st, ds = stages(ctx, t), deals(ctx, t)
        owner = ctx.text("owner_id")
        if owner:
            ds = [d for d in ds if d.get("owner_id") == owner]
        names = {c["contact_id"]: c["name"] for c in contacts(ctx, t)}
        ds = [{**d, "contact_name": names.get(d.get("contact_id"), ""), "company_name": names.get(d.get("company_id"), "")} for d in ds]
        cols = board(st, ds, _last_touch(activities(ctx, t)), today(ctx))
        return {"stages": cols, "open_value": sum(c["value"] for c in cols), "weighted": sum(c["weighted"] for c in cols),
                "won": [d for d in ds if d.get("state") == "won"][-20:], "lost": [d for d in ds if d.get("state") == "lost"][-20:]}
    run(ctx, body)


def timeline(ctx: RequestContext) -> None:
    def body(t):
        row = mine(ctx, CONTACTS, ctx.text("contact_id"), t)
        if row is None:
            raise ValueError("UNKNOWN_CONTACT")
        c = plain(row, "contact_id")
        ids = {c["contact_id"]}
        people = contacts(ctx, t, company_id=c["contact_id"]) if c["kind"] == "company" else []
        ids |= {p["contact_id"] for p in people}
        acts = sorted((a for a in activities(ctx, t) if a.get("contact_id") in ids), key=lambda a: a["at"], reverse=True)
        company = plain(mine(ctx, CONTACTS, c["company_id"], t), "contact_id") if c.get("company_id") and mine(ctx, CONTACTS, c["company_id"], t) else None
        return {"contact": c, "company": company, "people": people, "deals": [d for d in deals(ctx, t) if d.get("contact_id") in ids or d.get("company_id") in ids],
                "activities": acts, "open_tasks": [a for a in acts if not a.get("done")]}
    run(ctx, body)


def agenda(ctx: RequestContext) -> None:
    def body(t):
        day, owner = today(ctx), ctx.text("owner_id")
        names = {c["contact_id"]: c["name"] for c in contacts(ctx, t)}
        out = {"overdue": [], "today": [], "upcoming": []}
        for a in sorted(activities(ctx, t), key=lambda a: a.get("due") or a["at"]):
            if not a.get("done") and (not owner or a.get("owner_id") == owner):
                out[bucket(a, day)].append({**a, "contact_name": names.get(a.get("contact_id"), "")})
        return {**out, "today_date": day}
    run(ctx, body)


def insights_view(ctx: RequestContext) -> None:
    run(ctx, lambda t: {"insights": insights(stages(ctx, t), deals(ctx, t))})
