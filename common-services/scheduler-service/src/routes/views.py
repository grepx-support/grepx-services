# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""PREVIEW, SCHEDULES, TICKS, HEALTH - reading: a rule's words and next times before it is saved, an organisation's
schedules, one schedule's latest ticks (newest first, with how each went), and whether the ticker is alive."""
from datetime import datetime, timezone

from grepx_service import RequestContext

from dto import HEALTH_TABLE, SCHEDULES_TABLE, TICKS_TABLE, ScheduleField as F
from . import common
from .common import described, mine, plain

ALIVE_SECONDS = 180


def preview(ctx: RequestContext) -> None:
    try:
        out = described({k.value: ctx.get(k) for k in (F.KIND, F.EVERY_MINUTES, F.AT, F.CRON, F.TIMEZONE)})
    except ValueError as exc:
        return ctx.reject(str(exc.args[0]))
    ctx.accept({"words": out[F.WORDS.value], "next_runs": [x for x in out[F.NEXT_RUNS.value].split(",") if x]})


def schedules(ctx: RequestContext) -> None:
    eq = {F.TENANT_ID.value: ctx.text(F.TENANT_ID), **({F.OWNER.value: ctx.text(F.OWNER)} if ctx.text(F.OWNER) else {})}
    rows = [plain(r) for r in ctx.read.accepted(SCHEDULES_TABLE, **eq)]
    ctx.accept({"schedules": sorted(rows, key=lambda r: r[F.SCHEDULE_ID.value])})


def ticks(ctx: RequestContext) -> None:
    s = mine(ctx)
    if s is None:
        return ctx.reject("UNKNOWN_SCHEDULE")
    rows = [{**{k: v for k, v in r.items() if not k.startswith("_")}, "tick": r["_key"]}
            for r in ctx.read.rows(TICKS_TABLE, **{F.SCHEDULE_ID.value: s[F.SCHEDULE_ID.value]})]
    rows.sort(key=lambda r: (str(r.get(F.SLOT.value) or ""), r["tick"]), reverse=True)
    ctx.accept({"ticks": rows[: int(ctx.get(F.LIMIT, 20) or 20)]})


def health(ctx: RequestContext) -> None:
    at = float((ctx.read.one(HEALTH_TABLE, "ticker") or {}).get("at") or 0)
    ctx.accept({"alive": bool(at) and common.CLOCK().timestamp() - at < ALIVE_SECONDS, "at": datetime.fromtimestamp(at, timezone.utc).isoformat() if at else ""})
