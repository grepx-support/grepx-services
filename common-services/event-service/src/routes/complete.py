# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""COMPLETE — close the event on/after its date. Booking and rewards services react to the new state."""
from grepx_service import RequestContext, now_iso, today_iso

from dto import EventField as F, EventState, ReasonCode
from .common import load, save


def handle(ctx: RequestContext) -> None:
    event = load(ctx, ctx.text(F.EVENT_ID))
    if event is None:
        return ctx.reject(ReasonCode.UNKNOWN_EVENT)
    if event.get(F.STATE.value) == EventState.COMPLETED.value:
        return ctx.reject(ReasonCode.ALREADY_COMPLETED)
    if today_iso() < event[F.EVENT_DATE.value]:
        return ctx.reject(ReasonCode.TOO_EARLY)
    save(ctx, {**event, F.STATE.value: EventState.COMPLETED.value, F.COMPLETED_AT.value: now_iso(),
               F.COMPLETED_BY.value: ctx.text(F.ACTOR_ID), F.VOUCHER.value: dict(ctx.get(F.VOUCHER, {}))})
