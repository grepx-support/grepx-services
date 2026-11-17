# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ai-service actions. ASK and CHAT check the switch and the month's limit, then record a job (state thinking) and
answer at once; jobs.answer gives it to the model. CHAT_DELETE, USAGE."""
from __future__ import annotations

from grepx_service import ActionDispatcher, RequestContext, new_key, now_iso

from domain import HISTORY, month, system_prompt, title_of, with_data
from dto import AI_CHATS, AI_JOBS, AI_USAGE, AiAction as A, JobState, ReasonCode as R

PROMPT_FIELDS = ("product", "business", "currency", "today", "context", "instructions")


class Stop(Exception):
    pass


def run(ctx: RequestContext, body) -> None:
    tenant = ctx.text("tenant_id")
    if not tenant:
        return ctx.reject(R.MISSING_TENANT)
    try:
        ctx.accept(body(tenant))
    except Stop as stop:
        ctx.reject(*stop.args)


def usage_row(ctx: RequestContext, tenant: str, m: str) -> dict:
    row = ctx.read.accepted_one(AI_USAGE, f"{tenant}:{m}") or {}
    return {"tenant_id": tenant, "month": m, "calls": int(row.get("calls") or 0), "by_feature": dict(row.get("by_feature") or {})}


def allowed(ctx: RequestContext, tenant: str) -> int:
    if ctx.get("enabled") is False:
        raise Stop(R.AI_OFF)
    limit = int(ctx.get("limit") or 300)
    use = usage_row(ctx, tenant, month(now_iso()))
    if use["calls"] >= limit:
        raise Stop(R.LIMIT_REACHED, f"{use['calls']} of {limit} used this month")
    return limit


def job(ctx: RequestContext, tenant: str, feature: str, system: str, messages: list, chat_id: str = "") -> dict:
    key = new_key()[:20]
    row = {"job_id": key, "tenant_id": tenant, "user_id": ctx.text("actor_id"), "feature": feature[:40] or "ask", "state": JobState.THINKING.value,
           "system": system, "messages": messages, "model": ctx.text("model")[:60], "max_tokens": max(100, min(int(ctx.get("max_tokens") or 700), 2000)),
           "asked_at": now_iso(), **({"chat_id": chat_id} if chat_id else {})}
    ctx.emitter.submit(AI_JOBS, key, "ACCEPTED", row)
    return {k: row[k] for k in ("job_id", "state", "feature", "asked_at")}


def ask(ctx: RequestContext) -> None:
    def body(tenant):
        if not ctx.text("question"):
            raise Stop(R.NO_QUESTION)
        limit = allowed(ctx, tenant)
        raw = {k: ctx.get(k) for k in PROMPT_FIELDS}
        return {"job": job(ctx, tenant, ctx.text("feature"), system_prompt(raw), [{"role": "user", "content": with_data(ctx.text("question"), ctx.get("data"))}]),
                "limit": limit}
    run(ctx, body)


def chat(ctx: RequestContext) -> None:
    """A message in one of this person's chats: the last messages and today's business data go to the model."""
    def body(tenant):
        text, me = ctx.text("message")[:4000], ctx.text("actor_id")
        if not text:
            raise Stop(R.NO_QUESTION)
        allowed(ctx, tenant)
        key = ctx.text("chat_id")
        old = ctx.read.accepted_one(AI_CHATS, key) if key else None
        if key and (old is None or old.get("tenant_id") != tenant or old.get("user_id") != me):
            raise Stop(R.UNKNOWN_CHAT)
        if old and old.get("thinking"):
            raise Stop(R.BUSY)
        key = key or new_key()[:20]
        msgs = [x for x in (old or {}).get("messages") or [] if not x.get("pending")]
        history = [{"role": x["role"], "content": x["content"]} for x in msgs if x.get("content") and not x.get("failed")][-HISTORY:]
        raw = {k: ctx.get(k) for k in PROMPT_FIELDS}
        asked = job(ctx, tenant, "chat", system_prompt(raw), [*history, {"role": "user", "content": with_data(text, ctx.get("data"))}], key)
        msgs.append({"role": "user", "content": text, "at": now_iso()})
        row = {"chat_id": key, "tenant_id": tenant, "user_id": me, "product": ctx.text("product"), "title": (old or {}).get("title") or title_of(text),
               "messages": msgs, "thinking": asked["job_id"], "created_at": (old or {}).get("created_at") or now_iso(), "updated_at": now_iso()}
        ctx.emitter.submit(AI_CHATS, key, "ACCEPTED", row)
        return {"chat": row, "job": asked}
    run(ctx, body)


def chat_delete(ctx: RequestContext) -> None:
    def body(tenant):
        old = ctx.read.accepted_one(AI_CHATS, ctx.text("chat_id"))
        if old is None or old.get("tenant_id") != tenant or old.get("user_id") != ctx.text("actor_id"):
            raise Stop(R.UNKNOWN_CHAT)
        ctx.emitter.submit(AI_CHATS, ctx.text("chat_id"), "ACCEPTED", {**{k: v for k, v in old.items() if not k.startswith("_") and k != "status"},
                                                                       "deleted": True, "messages": [], "updated_at": now_iso()})
        return {"deleted": ctx.text("chat_id")}
    run(ctx, body)


def usage(ctx: RequestContext) -> None:
    run(ctx, lambda tenant: {"usage": usage_row(ctx, tenant, month(now_iso())), "limit": int(ctx.get("limit") or 300)})


handle = ActionDispatcher({A.ASK: ask, A.CHAT: chat, A.CHAT_DELETE: chat_delete, A.USAGE: usage}, A, "ai_requests")
