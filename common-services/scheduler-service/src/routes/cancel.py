# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CANCEL — stop a schedule."""
from grepx_service import RequestContext

from dto import SCHEDULES_TABLE, ScheduleField as F


def handle(ctx: RequestContext) -> None:
    ctx.emitter.submit(SCHEDULES_TABLE, ctx.text(F.SCHEDULE_ID), "CANCELLED", {F.SCHEDULE_ID.value: ctx.text(F.SCHEDULE_ID)})
