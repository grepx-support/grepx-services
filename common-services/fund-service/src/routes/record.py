# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RECORD - one movement of a fund. Refused when its currency is not the fund's (converting comes later), when a
promise / money in / payback names no party of the business, or when it would spend more than the fund has."""
from grepx_service import RequestContext, new_key, now_iso

from domain import NEEDS_PARTY, TAKES_CASH, clean_entry, currency, minor, totals
from dto import ENTRIES, FUNDS, PARTIES, ReasonCode
from .common import entries, mine, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    fund = mine(ctx, FUNDS, ctx.text("fund_id"), t)
    if fund is None:
        return ctx.reject(ReasonCode.UNKNOWN_FUND)
    try:
        e = clean_entry(ctx.fields)
        cur = currency(ctx.text("currency") or fund["currency"])
        amount = minor(ctx.get("amount"), cur)
    except ValueError as exc:
        return ctx.reject(str(exc))
    if cur != fund["currency"]:
        return ctx.reject(ReasonCode.CURRENCY_MISMATCH)
    if e["kind"] in NEEDS_PARTY and mine(ctx, PARTIES, e["party_id"], t) is None:
        return ctx.reject(ReasonCode.UNKNOWN_PARTY)
    loan = fund.get("kind") == "loan"
    if e["kind"] in TAKES_CASH and not (loan and e["kind"] == "return") and amount > totals(entries(ctx, t, fund_id=fund["_key"]), loan)["available"]:
        return ctx.reject(ReasonCode.NOT_ENOUGH_AVAILABLE)
    row = {**e, "fund_id": fund["_key"], "amount": amount, "currency": cur, "tenant_id": t, "at": now_iso(), "by": ctx.text("actor_name"),
           "reversed": False}
    key = new_key()[:14]
    ctx.emitter.submit(ENTRIES, key, "ACCEPTED", row)
    ctx.accept({"entry": {**row, "entry_id": key}})


def reverse(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    row = mine(ctx, ENTRIES, ctx.text("entry_id"), t)
    if row is None:
        return ctx.reject(ReasonCode.UNKNOWN_ENTRY)
    if row.get("reversed"):
        return ctx.reject(ReasonCode.ALREADY_REVERSED)
    done = {**{k: v for k, v in row.items() if not k.startswith("_") and k != "status"}, "reversed": True,
            "reversed_by": ctx.text("actor_name"), "reversed_at": now_iso(), "reverse_reason": ctx.text("reason")[:200]}
    ctx.emitter.submit(ENTRIES, row["_key"], "ACCEPTED", done)
    ctx.accept({"reversed": row["_key"]})
