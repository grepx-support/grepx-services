# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RECORD - one reading or one filled checklist, by whom and when. Out of range (or a "no") is kept, flagged, and
must carry the corrective action taken."""
from datetime import datetime

from grepx_service import RequestContext, new_key

from domain import judge
from dto import LOGS, ReasonCode
from .common import point, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    p = point(ctx, t, ctx.text("point_id"))
    if p is None:
        return ctx.reject(ReasonCode.UNKNOWN_POINT)
    try:
        result = judge(p, ctx.fields)
        at = datetime.fromisoformat(ctx.text("at")[:16]) if ctx.text("at") else datetime.now()
    except ValueError as exc:
        return ctx.reject(str(exc) if str(exc).isupper() else ReasonCode.INVALID_VALUE)
    action = " ".join(ctx.text("action_taken").split())[:300]
    if not result["ok"] and not action:
        return ctx.reject(ReasonCode.ACTION_NEEDED)
    row = {"tenant_id": t, "site_id": p["site_id"], "point_id": p["point_id"], "point_name": p["name"], "unit": p.get("unit", ""),
           "date": at.date().isoformat(), "at": at.isoformat(timespec="minutes"), "by": ctx.text("actor_name"), **result,
           "action_taken": action, "note": " ".join(ctx.text("note").split())[:300]}
    key = new_key()[:14]
    ctx.emitter.submit(LOGS, key, "ACCEPTED", row)
    ctx.accept({"record": {**row, "log_id": key}})
