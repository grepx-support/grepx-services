"""CHANGE_STATUS — move a task across the board (todo / in_progress / blocked / done)."""
from grepx_service import RequestContext

from domain import can_edit
from dto import ReasonCode, TaskField as F, TaskState
from .common import load, save


def handle(ctx: RequestContext) -> None:
    task = load(ctx)
    if task is None:
        return ctx.reject(ReasonCode.UNKNOWN_TASK)
    state = ctx.text(F.STATE)
    if state not in {s.value for s in TaskState}:
        return ctx.reject(ReasonCode.INVALID_STATE)
    if not can_edit(task, ctx.text(F.ACTOR_ID), bool(ctx.get(F.ACTOR_IS_MANAGER, False))):
        return ctx.reject(ReasonCode.NOT_ALLOWED)
    previous, task[F.STATE.value] = task.get(F.STATE.value), state
    save(ctx, task, "status", f"{previous} -> {state}")
