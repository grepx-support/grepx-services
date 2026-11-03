"""CLAIM — take an unassigned task."""
from grepx_service import RequestContext

from dto import ReasonCode, TaskField as F
from .common import load, save


def handle(ctx: RequestContext) -> None:
    task = load(ctx)
    if task is None:
        return ctx.reject(ReasonCode.UNKNOWN_TASK)
    if task.get(F.ASSIGNEE_ID.value):
        return ctx.reject(ReasonCode.ALREADY_ASSIGNED)
    for f in (F.ASSIGNEE_NAME, F.ASSIGNEE_EMAIL, F.ASSIGNEE_PHONE):
        task[f.value] = ctx.text(f)
    task[F.ASSIGNEE_ID.value] = ctx.text(F.ACTOR_ID)
    save(ctx, task, "claimed")
