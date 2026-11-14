# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""OVERVIEW (every fund: totals per currency and in the business currency, the position of the business-currency
funds - real spending per use, promises, forecast, suggestions - and the balance sheet as of a date) and FUND (one fund
in full). The caller supplies `spending` per use ({use: [{month, category, amount}]}) to link real costs."""
from datetime import date

from grepx_service import RequestContext

from domain import against_plan, balance_sheet, clean_plan, months, parties, position, project, totals, uses, utilisation
from dto import ReasonCode
from .common import entries, funds, party_names, tenant

ADD = ("committed", "received", "pending", "allocated", "spent", "returned", "costs", "available", "interest", "owed")


def in_base(fund_rows: list[dict], base: str) -> dict:
    """Business-wide totals in the business currency (funds in another currency at their rate_to_base)."""
    out = {k: 0 for k in ADD}
    for f in fund_rows:
        rate = 1 if f["currency"] == base else float(f.get("rate_to_base") or 0)
        for k in ADD:
            out[k] += round(f[k] * rate)
    out["unconverted"] = [f["name"] for f in fund_rows if f["currency"] != base and not f.get("rate_to_base")]
    return out


def overview(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    every, names, today = entries(ctx, t), party_names(ctx, t), ctx.text("today") or date.today().isoformat()
    every_fund = sorted(funds(ctx, t), key=lambda f: (f.get("order") or 0, f["name"].lower()))
    out, per_currency = [], {}
    for f in every_fund:
        mine = [e for e in every if e["fund_id"] == f["fund_id"]]
        tot = totals(mine, f.get("kind") == "loan")
        out.append({**f, **tot, "parties": len({e["party_id"] for e in mine if e.get("party_id")}),
                    "target_progress": round(tot["received"] / f["target"] * 100, 1) if f.get("target") else None})
        cur = per_currency.setdefault(f["currency"], {k: 0 for k in ADD})
        for k in ADD:
            cur[k] += tot[k]
    for cur in per_currency.values():
        cur["utilised_pct"] = round(cur["spent"] / cur["allocated"] * 100, 1) if cur["allocated"] else None
    base = ctx.text("base") or (every_fund[0]["currency"] if every_fund else "")
    home = [f for f in every_fund if f["currency"] == base]
    home_entries = [e for e in every if e["fund_id"] in {f["fund_id"] for f in home}]
    as_of = ctx.text("as_of")
    ctx.accept({"funds": out, "totals": per_currency, "base": base, "in_base": in_base(out, base),
                "balance_sheet": {c: balance_sheet([f for f in every_fund if f["currency"] == c], every, names, as_of) for c in per_currency},
                "position": position(home, home_entries, names, ctx.get("spending") or {}, today),
                "overdue": [p for p in position(every_fund, every, names, {}, today)["promises"] if p["overdue"]],
                "parties": [{"party_id": k, "name": v} for k, v in sorted(names.items(), key=lambda x: x[1])]})


def fund(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    f = next((x for x in funds(ctx, t) if x["fund_id"] == ctx.text("fund_id")), None)
    if f is None:
        return ctx.reject(ReasonCode.UNKNOWN_FUND)
    mine, names, today = entries(ctx, t, fund_id=f["fund_id"]), party_names(ctx, t), ctx.text("today") or date.today().isoformat()
    tot, plan = totals(mine, f.get("kind") == "loan"), f.get("plan") or clean_plan({})
    who = parties(mine, names)
    projected = project(plan, tot["received"]) if plan["uses"] else None
    for p in who:                                            # each party's expected payout over the horizon, by share
        p["projected_payout"] = round((projected or {}).get("paid_out", 0) * p["share_pct"] / 100)
        p["roi_pct"] = round((p["returned"] - p["received"]) / p["received"] * 100, 1) if p["received"] else None
    vs_plan = against_plan(plan, ctx.get("actuals") or {})
    pos = position([f], mine, names, ctx.get("spending") or {}, today, vs_plan)
    ctx.accept({"fund": f, "totals": tot, "parties": who, "uses": uses(mine), "months": months(mine), "utilisation": utilisation(mine),
                "plan": plan, "projection": projected, "against_plan": vs_plan, "overdue": [p for p in pos["promises"] if p["overdue"]],
                "linked": pos["linked"], "promises": pos["promises"], "forecast": pos["forecast"], "suggestions": pos["suggestions"],
                "balance_sheet": balance_sheet([f], mine, names, ctx.text("as_of")),
                "entries": [{**e, "party": names.get(e.get("party_id"), "")} for e in reversed(mine)]})
