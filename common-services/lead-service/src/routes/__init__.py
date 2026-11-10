# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for lead-service."""
import os

from grepx_service import ActionDispatcher, RequestContext, new_key, notify, now_iso, state_of

from domain import clean_lead
from dto import TABLE, LeadAction, LeadStatus, ReasonCode


def submit(ctx: RequestContext) -> None:
    try:
        lead = clean_lead({k: ctx.get(k) for k in ("name", "email", "phone", "company", "size", "message", "product", "kind", "website")})
    except ValueError as exc:
        return ctx.reject(str(exc))
    lead_id = new_key()[:12]
    row = {"lead_id": lead_id, **lead, "stage": LeadStatus.NEW.value, "created_at": now_iso(), "history": []}
    ctx.emitter.submit(TABLE, lead_id, "ACCEPTED", row)
    for email in [e.strip() for e in os.environ.get("LEADS_NOTIFY_EMAIL", "").split(",") if e.strip()]:
        notify(ctx.emitter, "demo_request", email=email, channels=["email"], ref=f"lead-{lead_id}", auto=False,
               values={k: lead[k] for k in ("name", "company", "email", "phone", "size", "message")})
    ctx.accept({"lead_id": lead_id})


def set_status(ctx: RequestContext) -> None:
    lead = ctx.read.accepted_one(TABLE, ctx.text("lead_id"))
    if lead is None:
        return ctx.reject(ReasonCode.UNKNOWN_LEAD)
    status = ctx.text("stage")
    if status not in {s.value for s in LeadStatus}:
        return ctx.reject(ReasonCode.INVALID_STATUS)
    entry = {"at": now_iso(), "stage": status, "note": ctx.text("note")[:500], "by": ctx.text("actor_name")}
    row = {**state_of(lead), "stage": status, "history": [*(lead.get("history") or []), entry]}
    ctx.emitter.submit(TABLE, lead["_key"], "ACCEPTED", row)
    ctx.accept({"lead": row})


handle = ActionDispatcher({LeadAction.SUBMIT: submit, LeadAction.SET_STATUS: set_status}, LeadAction, "lead_requests")
