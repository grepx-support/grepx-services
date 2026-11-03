"""REGISTER — create or replace a schedule (key = schedule_id, so re-registering at every start is idempotent)."""
from grepx_service import RequestContext

from dto import SCHEDULES_TABLE, ReasonCode, ScheduleField as F, ScheduleKind


def handle(ctx: RequestContext) -> None:
    schedule_id, job, target = ctx.text(F.SCHEDULE_ID), ctx.text(F.JOB), ctx.text(F.TARGET_SERVICE)
    if not (schedule_id and job and target):
        return ctx.reject(ReasonCode.MISSING_FIELD)
    kind = ctx.text(F.KIND)
    valid = (kind == ScheduleKind.EVERY_MINUTES.value and int(ctx.get(F.EVERY_MINUTES, 0)) > 0) or \
            (kind == ScheduleKind.DAILY_AT.value and len(ctx.text(F.AT)) == 5)
    if not valid:
        return ctx.reject(ReasonCode.INVALID_SCHEDULE)
    ctx.emitter.submit(SCHEDULES_TABLE, schedule_id, "ACCEPTED", {k.value: ctx.get(k) for k in F if ctx.get(k) is not None})
