"""UPDATE — edit fields; reassignment notifies the new assignee."""
from grepx_service import RequestContext

from domain import can_edit
from dto import EDITABLE, ReasonCode, TaskField as F, TaskState
from .common import load, notify_assignee, save


def handle(ctx: RequestContext) -> None:
    task = load(ctx)
    if task is None:
        return ctx.reject(ReasonCode.UNKNOWN_TASK)
    if not can_edit(task, ctx.text(F.ACTOR_ID), bool(ctx.get(F.ACTOR_IS_MANAGER, False))):
        return ctx.reject(ReasonCode.NOT_ALLOWED)
    if ctx.get(F.STATE) and ctx.text(F.STATE) not in {s.value for s in TaskState}:
        return ctx.reject(ReasonCode.INVALID_STATE)
    before = task.get(F.ASSIGNEE_ID.value)
    changed = [f.value for f in EDITABLE if ctx.get(f) is not None and ctx.get(f) != task.get(f.value)]
    task.update({f: ctx.get(f) for f in changed})
    save(ctx, task, "edited", ", ".join(changed))
    if task.get(F.ASSIGNEE_ID.value) != before:
        notify_assignee(ctx, task)
