# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_PLAN - a fund's plan: horizon, discount rate, share of EBITDA paid out, hurdle, and per use the EBITDA it is
expected to make a month, when it starts and its ramp-up."""
from grepx_service import RequestContext

from domain import clean_plan
from dto import FUNDS, ReasonCode
from .common import mine, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    fund = mine(ctx, FUNDS, ctx.text("fund_id"), t)
    if fund is None:
        return ctx.reject(ReasonCode.UNKNOWN_FUND)
    try:
        plan = clean_plan(ctx.get("plan") or {})
    except ValueError as exc:
        return ctx.reject(str(exc))
    ctx.emitter.submit(FUNDS, fund["_key"], "ACCEPTED", {**{k: v for k, v in fund.items() if not k.startswith("_") and k != "status"}, "plan": plan})
    ctx.accept({"plan": plan})
