# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""REMOVE_SHIFT - take a shift off the roster."""
from grepx_service import RequestContext

from dto import SHIFTS, ReasonCode
from .common import tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    row = ctx.read.accepted_one(SHIFTS, ctx.text("shift_id"))
    if row is None or row.get("tenant_id") != t:
        return ctx.reject(ReasonCode.UNKNOWN_SHIFT)
    ctx.emitter.submit(SHIFTS, row["_key"], "DELETED", {"tenant_id": t})
    ctx.accept({"removed": row["_key"]})
