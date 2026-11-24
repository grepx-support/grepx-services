# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""REGISTER - create or change a schedule (key = schedule_id, so registering again at every start is idempotent). A new
or changed rule fires only for times after now - never a burst of the slots it would have had."""
from grepx_service import RequestContext

from dto import ScheduleField as F
from . import common
from .common import keep, mine, rule

RULE = (F.KIND, F.EVERY_MINUTES, F.AT, F.CRON, F.TIMEZONE)


def handle(ctx: RequestContext) -> None:
    schedule_id, job, target = ctx.text(F.SCHEDULE_ID), ctx.text(F.JOB), ctx.text(F.TARGET_SERVICE)
    if not (schedule_id and job and target):
        return ctx.reject("MISSING_FIELD")
    fields = {k.value: ctx.get(k) for k in F if ctx.get(k) is not None and k not in (F.WORDS, F.NEXT_RUNS, F.LAST_FIRED, F.SINCE)}
    try:
        rule(fields)
    except ValueError as exc:
        return ctx.reject(str(exc.args[0]))
    cur = mine(ctx) or {}
    same = cur and all(str(cur.get(k.value) or "") == str(fields.get(k.value) or "") for k in RULE)
    since = cur.get(F.SINCE.value) if same else common.CLOCK().isoformat()
    keep(ctx, {**cur, F.PAUSED.value: bool(cur.get(F.PAUSED.value, False)), **fields, F.SINCE.value: since})
