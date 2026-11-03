# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CREATE — a new task (state todo unless given)."""
from grepx_service import RequestContext

from dto import EDITABLE, ReasonCode, TaskField as F, TaskState
from .common import notify_assignee, save


def handle(ctx: RequestContext) -> None:
    title = ctx.text(F.TITLE)
    if not title:
        return ctx.reject(ReasonCode.MISSING_FIELD)
    task = {f.value: ctx.get(f) for f in EDITABLE if ctx.get(f) is not None}
    task.update({F.TASK_ID.value: ctx.text(F.TASK_ID) or ctx.key, F.TITLE.value: title[:200], F.CREATED_BY.value: ctx.text(F.ACTOR_ID),
                 F.TENANT_ID.value: ctx.text(F.TENANT_ID), F.STATE.value: ctx.text(F.STATE) or TaskState.TODO.value})
    if task[F.STATE.value] not in {s.value for s in TaskState}:
        return ctx.reject(ReasonCode.INVALID_STATE)
    save(ctx, task, "created", ctx.text(F.PHASE))
    notify_assignee(ctx, task)
