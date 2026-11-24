# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Shared by the routes: the clock, a schedule's rule from its fields, the fields kept with a schedule (its rule in words,
its next times), reading one of the organisation's schedules, and saving one."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional

from grepx_service import RequestContext

from domain import Rule, rule_of
from dto import NEXT_SHOWN, SCHEDULES_TABLE, ScheduleField as F

CLOCK: Callable[[], datetime] = lambda: datetime.now(timezone.utc)      # tests set another clock


def rule(fields: dict) -> Rule:
    return rule_of(str(fields.get(F.KIND.value) or ""), int(fields.get(F.EVERY_MINUTES.value) or 0), str(fields.get(F.AT.value) or ""),
                   str(fields.get(F.CRON.value) or ""), str(fields.get(F.TIMEZONE.value) or ""))


def described(fields: dict, now: Optional[datetime] = None) -> dict:
    """The fields with the rule in words and its next times (none while paused)."""
    r, now = rule(fields), now or CLOCK()
    nxt = [] if fields.get(F.PAUSED.value) else [t.isoformat() for t in r.upcoming(now, NEXT_SHOWN)]
    return {**fields, F.WORDS.value: r.words, F.NEXT_RUNS.value: ",".join(nxt)}


KEPT = {f.value for f in F}


def plain(row: dict) -> dict:
    """A stored schedule's own fields (not the routing a row carries)."""
    return {**{k: v for k, v in row.items() if k in KEPT}, F.SCHEDULE_ID.value: row["_key"]}


def mine(ctx: RequestContext) -> Optional[dict]:
    """The schedule asked for, when it is this organisation's (a request without tenant_id is a service's own)."""
    row = ctx.read.accepted_one(SCHEDULES_TABLE, ctx.text(F.SCHEDULE_ID))
    if row is None or row.get(F.TENANT_ID.value, "") != ctx.text(F.TENANT_ID):
        return None
    return plain(row)


def keep(ctx: RequestContext, fields: dict) -> dict:
    """Save the schedule (its rule described again) and answer with it."""
    out = described({k: v for k, v in fields.items() if v is not None})
    ctx.emitter.submit(SCHEDULES_TABLE, out[F.SCHEDULE_ID.value], "ACCEPTED", out)
    ctx.accept({"schedule": out})
    return out


def changed(ctx: RequestContext, change: Callable[[dict], dict]) -> None:
    """PAUSE / RESUME and the like: the schedule, changed, kept - or UNKNOWN_SCHEDULE."""
    cur = mine(ctx)
    if cur is None:
        return ctx.reject("UNKNOWN_SCHEDULE")
    keep(ctx, change(cur))
