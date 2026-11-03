# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Task projection helpers: load, save with an audit event, notify the assignee."""
from __future__ import annotations

from typing import Optional

from grepx_service import RequestContext, notify, now_iso, state_of

from dto import TASKS_TABLE, TaskField as F


def load(ctx: RequestContext) -> Optional[dict]:
    task = ctx.read.accepted_one(TASKS_TABLE, ctx.text(F.TASK_ID))
    return state_of(task)


def save(ctx: RequestContext, task: dict, action: str, detail: str = "", status: str = "ACCEPTED") -> None:
    task = state_of(task)
    events = list(task.get(F.EVENTS.value) or [])
    events.append({"at": now_iso(), "by": ctx.text(F.ACTOR_ID), "action": action, "detail": detail})
    task[F.EVENTS.value] = events[-50:]
    ctx.emitter.submit(TASKS_TABLE, task[F.TASK_ID.value], status, task)
    ctx.accept({F.TASK_ID: task[F.TASK_ID.value]})


def notify_assignee(ctx: RequestContext, task: dict, template: str = "task_assigned") -> None:
    if not task.get(F.ASSIGNEE_ID.value) or task.get(F.ASSIGNEE_ID.value) == ctx.text(F.ACTOR_ID):
        return
    notify(ctx.emitter, template, email=task.get(F.ASSIGNEE_EMAIL.value, ""), phone=task.get(F.ASSIGNEE_PHONE.value, ""),
           values={"first_name": (task.get(F.ASSIGNEE_NAME.value) or "").split(" ")[0], "title": task.get(F.TITLE.value),
                   "due": (task.get(F.DUE_AT.value) or "").replace("T", " "), "context": task.get(F.REF_LABEL.value) or "General",
                   "link": ctx.text(F.LINK)},
           ref=f"{task[F.TASK_ID.value]}-{task.get(F.ASSIGNEE_ID.value)}", tenant_id=task.get(F.TENANT_ID.value, ""),
           user_id=task.get(F.ASSIGNEE_ID.value, ""))
