"""CANCEL — stop a schedule."""
from grepx_service import RequestContext

from dto import SCHEDULES_TABLE, ScheduleField as F


def handle(ctx: RequestContext) -> None:
    ctx.emitter.submit(SCHEDULES_TABLE, ctx.text(F.SCHEDULE_ID), "CANCELLED", {F.SCHEDULE_ID.value: ctx.text(F.SCHEDULE_ID)})
