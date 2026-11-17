# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ai-service actions: ASK (counted against the business's monthly limit) and USAGE. The model call is
domain.call_model; tests replace MODEL_CALL."""
from __future__ import annotations

from grepx_service import ActionDispatcher, RequestContext, now_iso

import domain
from domain import month, prompt
from dto import AI_USAGE, AiAction as A, ReasonCode as R

MODEL_CALL = domain.call_model


def usage_row(ctx: RequestContext, tenant: str, m: str) -> dict:
    row = ctx.read.accepted_one(AI_USAGE, f"{tenant}:{m}") or {}
    return {"tenant_id": tenant, "month": m, "calls": int(row.get("calls") or 0), "by_feature": dict(row.get("by_feature") or {})}


def ask(ctx: RequestContext) -> None:
    tenant = ctx.text("tenant_id")
    if not tenant:
        return ctx.reject(R.MISSING_TENANT)
    if not ctx.text("question"):
        return ctx.reject(R.NO_QUESTION)
    if ctx.get("enabled") is False:
        return ctx.reject(R.AI_OFF)
    m = month(now_iso())
    use = usage_row(ctx, tenant, m)
    limit = int(ctx.get("limit") or 300)
    if use["calls"] >= limit:
        return ctx.reject(R.LIMIT_REACHED, f"{use['calls']} of {limit} used this month")
    system, user = prompt({k: ctx.get(k) for k in ("product", "business", "currency", "today", "instructions", "question", "data")})
    try:
        answer = MODEL_CALL(system, user, max(100, min(int(ctx.get("max_tokens") or 700), 2000)))
    except KeyError:
        return ctx.reject(R.NO_KEY)
    except RuntimeError as exc:
        return ctx.reject(R.MODEL_FAILED, str(exc)[:200])
    feature = ctx.text("feature")[:40] or "ask"
    use["calls"] += 1
    use["by_feature"][feature] = use["by_feature"].get(feature, 0) + 1
    ctx.emitter.submit(AI_USAGE, f"{tenant}:{m}", "ACCEPTED", {**use, "last_at": now_iso()})
    ctx.accept({"answer": answer, "used": use["calls"], "limit": limit})


def usage(ctx: RequestContext) -> None:
    tenant = ctx.text("tenant_id")
    if not tenant:
        return ctx.reject(R.MISSING_TENANT)
    ctx.accept({"usage": usage_row(ctx, tenant, month(now_iso())), "limit": int(ctx.get("limit") or 300)})


handle = ActionDispatcher({A.ASK: ask, A.USAGE: usage}, A, "ai_requests")
