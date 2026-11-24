# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RUN_NOW - one tick to the target at once, outside the rule (marked manual)."""
from grepx_service import RequestContext

from domain.rules import slot_of
from dto import TICKS_TABLE, ScheduleField as F
from . import common
from .common import mine


def handle(ctx: RequestContext) -> None:
    s = mine(ctx)
    if s is None:
        return ctx.reject("UNKNOWN_SCHEDULE")
    now = common.CLOCK()
    key = f"{s[F.SCHEDULE_ID.value]}-now-{now:%Y%m%dT%H%M%S}"
    ctx.request(TICKS_TABLE, key, {**ticket(s, slot_of(now)), F.MANUAL.value: True}, s[F.TARGET_SERVICE.value])
    ctx.accept({"tick": key})


def ticket(s: dict, slot: str) -> dict:
    """What a tick carries to its target: which schedule, job and slot, its label, the organisation and the payload."""
    return {F.SCHEDULE_ID.value: s[F.SCHEDULE_ID.value], F.JOB.value: s.get(F.JOB.value), F.SLOT.value: slot,
            **{k.value: s.get(k.value) for k in (F.TENANT_ID, F.OWNER, F.LABEL, F.PAYLOAD) if s.get(k.value) is not None}}
