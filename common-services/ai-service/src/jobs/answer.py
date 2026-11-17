# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Answer one job: call the model, count it, store the answer on the job (and in the chat it belongs to)."""
from __future__ import annotations

from grepx_service import Emitter, Reader, now_iso

import domain
from domain import month
from dto import AI_CHATS, AI_JOBS, AI_USAGE, JobState, ReasonCode

MODEL_CALL = None        # tests set a stand-in; None = domain.call_model


def answer(app, row, cfg) -> str:
    job = {k: v for k, v in row.fields.items() if not k.startswith("_") and k != "status"}
    if job.get("state") != JobState.THINKING.value:
        return "skipped"
    read, emit = Reader(app.client), Emitter(app, cfg, cause=row)
    call = MODEL_CALL or domain.call_model
    try:
        text = call(job["system"], job["messages"], int(job.get("max_tokens") or 700), job.get("model", ""))
        done = {**job, "state": JobState.DONE.value, "answer": text, "answered_at": now_iso()}
    except KeyError:
        done = {**job, "state": JobState.FAILED.value, "reason": ReasonCode.NO_KEY.value, "answered_at": now_iso()}
    except Exception as exc:              # noqa: BLE001 - any failure of the engine is a failed answer, never a lost job
        done = {**job, "state": JobState.FAILED.value, "reason": ReasonCode.MODEL_FAILED.value, "detail": str(exc)[:200], "answered_at": now_iso()}
    done.pop("system", None)              # the prompt is not kept once answered (it carried the business's data)
    done["messages"] = done["messages"][-1:]
    emit.submit(AI_JOBS, row.key, "ACCEPTED", done)
    if done["state"] == JobState.DONE.value:
        m = month(now_iso())
        use = read.accepted_one(AI_USAGE, f"{job['tenant_id']}:{m}") or {}
        by = dict(use.get("by_feature") or {})
        by[job.get("feature", "ask")] = by.get(job.get("feature", "ask"), 0) + 1
        emit.submit(AI_USAGE, f"{job['tenant_id']}:{m}", "ACCEPTED",
                    {"tenant_id": job["tenant_id"], "month": m, "calls": int(use.get("calls") or 0) + 1, "by_feature": by, "last_at": now_iso()})
    if job.get("chat_id"):
        chat = read.accepted_one(AI_CHATS, job["chat_id"])
        if chat:
            msgs = [x for x in chat.get("messages") or [] if not x.get("pending")]
            msgs.append({"role": "assistant", "content": done.get("answer") or "", "at": now_iso(), "job_id": row.key,
                         **({"failed": done.get("reason")} if done["state"] == JobState.FAILED.value else {})})
            emit.submit(AI_CHATS, job["chat_id"], "ACCEPTED", {**{k: v for k, v in chat.items() if not k.startswith("_") and k != "status"},
                                                                "messages": msgs, "thinking": "", "updated_at": now_iso()})
    return done["state"]
