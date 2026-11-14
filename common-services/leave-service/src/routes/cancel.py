# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CANCEL - take back a pending or approved leave that has not started yet."""
from datetime import date

from grepx_service import RequestContext

from dto import LEAVES, LeaveState, ReasonCode
from .common import plain, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    row = ctx.read.accepted_one(LEAVES, ctx.text("leave_id"))
    if row is None or row.get("tenant_id") != t or row.get("state") not in (LeaveState.PENDING.value, LeaveState.APPROVED.value):
        return ctx.reject(ReasonCode.UNKNOWN_LEAVE)
    if row.get("state") == LeaveState.APPROVED.value and row["first"] <= (ctx.text("today") or date.today().isoformat()):
        return ctx.reject(ReasonCode.ALREADY_STARTED)
    ctx.emitter.submit(LEAVES, row["_key"], "ACCEPTED", {**plain(row), "state": LeaveState.CANCELLED.value})
    ctx.accept({"cancelled": row["_key"]})
