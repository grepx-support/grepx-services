# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""DELETE — remove a task (kept in history as DELETED)."""
from grepx_service import RequestContext

from domain import can_edit
from dto import ReasonCode, TaskField as F
from .common import load, save


def handle(ctx: RequestContext) -> None:
    task = load(ctx)
    if task is None:
        return ctx.reject(ReasonCode.UNKNOWN_TASK)
    if not can_edit(task, ctx.text(F.ACTOR_ID), bool(ctx.get(F.ACTOR_IS_MANAGER, False))):
        return ctx.reject(ReasonCode.NOT_ALLOWED)
    save(ctx, task, "deleted", status="DELETED")
