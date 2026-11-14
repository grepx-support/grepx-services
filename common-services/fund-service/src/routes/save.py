# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_FUND and SAVE_PARTY - add or change a fund (its currency is fixed once money moved) or a party."""
from grepx_service import RequestContext, new_key

from domain import clean_fund, currency, minor
from dto import ENTRIES, FUNDS, PARTIES, ReasonCode
from .common import mine, tenant


def fund(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    fid = ctx.text("fund_id")
    current = mine(ctx, FUNDS, fid, t)
    if fid and current is None:
        return ctx.reject(ReasonCode.UNKNOWN_FUND)
    try:
        row = clean_fund({**(current or {}), **{k: v for k, v in ctx.fields.items() if v is not None}})
        cur = currency(ctx.text("currency") or (current or {}).get("currency"))
        target = minor(ctx.get("target"), cur) if ctx.get("target") not in (None, "", 0, "0") else (current or {}).get("target", 0)
    except ValueError as exc:
        return ctx.reject(str(exc))
    if current and cur != current["currency"] and ctx.read.accepted(ENTRIES, tenant_id=t, fund_id=fid):
        return ctx.reject(ReasonCode.CURRENCY_MISMATCH)
    fid = fid or new_key()[:12]
    full = {**row, "currency": cur, "target": target, "tenant_id": t}
    ctx.emitter.submit(FUNDS, fid, "ACCEPTED", full)
    ctx.accept({"fund": {**full, "fund_id": fid}})


def party(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    pid = ctx.text("party_id")
    if pid and mine(ctx, PARTIES, pid, t) is None:
        return ctx.reject(ReasonCode.UNKNOWN_PARTY)
    name = " ".join(ctx.text("name").split())[:80]
    if not name:
        return ctx.reject(ReasonCode.INVALID_NAME)
    pid = pid or new_key()[:12]
    row = {"name": name, "kind": ctx.text("kind") or "investor", "email": ctx.text("email")[:120], "phone": ctx.text("phone")[:20],
           "note": ctx.text("note")[:300], "tenant_id": t}
    ctx.emitter.submit(PARTIES, pid, "ACCEPTED", row)
    ctx.accept({"party": {**row, "party_id": pid}})
