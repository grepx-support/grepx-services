# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""STATEMENT - one party's statement for a period (default: everything to today) - and SEND_STATEMENT: email /
WhatsApp it with the PDF the caller made attached, in the deployment's words for the role "fund_statement"
(values: org, name, period). Each send is kept on the party."""
from datetime import date

from grepx_service import RequestContext, notify, now_iso
from grepx_service.plugins import template_for

from domain import statement
from dto import PARTIES, ReasonCode
from .common import entries, funds, mine, party_names, plain, tenant


def period(ctx: RequestContext) -> tuple[str, str]:
    return ctx.text("first") or "0000-01-01", ctx.text("last") or ctx.text("today") or date.today().isoformat()


def build(ctx: RequestContext, t: str, party_id: str) -> dict:
    first, last = period(ctx)
    return statement(party_id, funds(ctx, t), entries(ctx, t), party_names(ctx, t), first, last)


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    if mine(ctx, PARTIES, ctx.text("party_id"), t) is None:
        return ctx.reject(ReasonCode.UNKNOWN_PARTY)
    ctx.accept({"statement": build(ctx, t, ctx.text("party_id"))})


def send(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    party = mine(ctx, PARTIES, ctx.text("party_id"), t)
    if party is None:
        return ctx.reject(ReasonCode.UNKNOWN_PARTY)
    channels = [c for c in ctx.get("channels") or ["email"] if (party.get("email") if c == "email" else party.get("phone"))]
    if not channels:
        return ctx.reject(ReasonCode.NO_CONTACT)
    first, last = period(ctx)
    sent = list(party.get("statements_sent") or [])
    notify(ctx.emitter, template_for(ctx.emitter.cfg, "fund_statement"), email=party.get("email", ""), phone=party.get("phone", ""),
           channels=channels, ref=f"statement-{party['_key']}-{len(sent)}", tenant_id=t, auto=False,
           attachments=[a for a in ctx.get("attachments") or [] if isinstance(a, dict)] or None,
           values={"name": party.get("name", ""), "org": ctx.text("org"), "period": f"{first if first > '0000' else 'the start'} to {last}"})
    sent.append({"at": now_iso(), "channels": channels, "first": first, "last": last, "by": ctx.text("actor_name")})
    row = {**plain(party, "party_id"), "statements_sent": sent}
    row.pop("party_id")
    ctx.emitter.submit(PARTIES, party["_key"], "ACCEPTED", row)
    ctx.accept({"party": {**row, "party_id": party["_key"]}})
