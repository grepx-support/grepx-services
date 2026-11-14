# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""DECIDE - approve or decline a pending leave, with an optional note."""
from grepx_service import RequestContext, now_iso

from dto import LEAVES, LeaveState, ReasonCode
from .common import plain, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    row = ctx.read.accepted_one(LEAVES, ctx.text("leave_id"))
    if row is None or row.get("tenant_id") != t:
        return ctx.reject(ReasonCode.UNKNOWN_LEAVE)
    if row.get("state") != LeaveState.PENDING.value:
        return ctx.reject(ReasonCode.ALREADY_DECIDED)
    state = LeaveState.APPROVED if ctx.get("approve") else LeaveState.DECLINED
    full = {**plain(row), "state": state.value, "decided_at": now_iso(), "decided_by": ctx.text("actor_name"), "decision_note": str(ctx.get("note") or "")[:300]}
    ctx.emitter.submit(LEAVES, row["_key"], "ACCEPTED", full)
    ctx.accept({"leave": {**full, "leave_id": row["_key"]}})
