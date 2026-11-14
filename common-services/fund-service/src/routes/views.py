# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""OVERVIEW (every fund, totals per currency, overdue promises) and FUND (one fund in full)."""
from datetime import date

from grepx_service import RequestContext

from domain import against_plan, balance_sheet, clean_plan, months, overdue, parties, project, totals, uses, utilisation
from dto import ReasonCode
from .common import entries, funds, party_names, tenant

ADD = ("committed", "received", "pending", "allocated", "spent", "returned", "costs", "available", "interest", "owed")


def overview(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    every, names, today = entries(ctx, t), party_names(ctx, t), ctx.text("today") or date.today().isoformat()
    out, per_currency = [], {}
    for f in funds(ctx, t):
        mine = [e for e in every if e["fund_id"] == f["fund_id"]]
        tot = totals(mine, f.get("kind") == "loan")
        out.append({**f, **tot, "parties": len({e["party_id"] for e in mine if e.get("party_id")}),
                    "target_progress": round(tot["received"] / f["target"] * 100, 1) if f.get("target") else None})
        cur = per_currency.setdefault(f["currency"], {k: 0 for k in ADD})
        for k in ADD:
            cur[k] += tot[k]
    late = [{**o, "name": names.get(o["party_id"], "?")} for o in overdue(every, today)]
    for cur in per_currency.values():
        cur["utilised_pct"] = round(cur["spent"] / cur["allocated"] * 100, 1) if cur["allocated"] else None
    sheets = {c: balance_sheet([f for f in funds(ctx, t) if f["currency"] == c], every) for c in per_currency}
    ctx.accept({"funds": out, "totals": per_currency, "balance_sheet": sheets, "overdue": late, "parties": [{"party_id": k, "name": v} for k, v in sorted(names.items(), key=lambda x: x[1])]})


def fund(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    f = next((x for x in funds(ctx, t) if x["fund_id"] == ctx.text("fund_id")), None)
    if f is None:
        return ctx.reject(ReasonCode.UNKNOWN_FUND)
    mine, names = entries(ctx, t, fund_id=f["fund_id"]), party_names(ctx, t)
    late = [{**o, "name": names.get(o["party_id"], "?")} for o in overdue(mine, ctx.text("today") or date.today().isoformat())]
    tot, plan = totals(mine, f.get("kind") == "loan"), f.get("plan") or clean_plan({})
    who = parties(mine, names)
    forecast = project(plan, tot["received"]) if plan["uses"] else None
    for p in who:                                            # each party's expected payout over the horizon, by share
        p["projected_payout"] = round((forecast or {}).get("paid_out", 0) * p["share_pct"] / 100)
        p["roi_pct"] = round((p["returned"] - p["received"]) / p["received"] * 100, 1) if p["received"] else None
    ctx.accept({"fund": f, "totals": tot, "parties": who, "uses": uses(mine), "months": months(mine), "utilisation": utilisation(mine),
                "plan": plan, "projection": forecast, "against_plan": against_plan(plan, ctx.get("actuals") or {}),
                "overdue": late, "entries": [{**e, "party": names.get(e.get("party_id"), "")} for e in reversed(mine)]})
