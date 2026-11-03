# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""MARK — staff set attendance on the board. Attended / no-show only on the event day; not eligible any day;
completed events are locked."""
from grepx_service import RequestContext, today_iso

from domain import DAY_ONLY, RANK
from dto import ReasonCode, BookingField as F
from .common import event_of, existing, save


def handle(ctx: RequestContext) -> None:
    key, state = ctx.text(F.BOOKING_ID), ctx.text(F.STATE)
    reg = existing(ctx, key)
    if reg is None:
        return ctx.reject(ReasonCode.NOT_REGISTERED)
    if state not in RANK or state == "cancelled":
        return ctx.reject(ReasonCode.INVALID_STATE)
    ctx.fields[F.EVENT_ID.value] = reg[F.EVENT_ID.value]
    event = event_of(ctx)
    if event is None or event.get("state") == "completed":
        return ctx.reject(ReasonCode.EVENT_CLOSED)
    if state in DAY_ONLY and today_iso() != event.get("event_date"):
        return ctx.reject(ReasonCode.NOT_EVENT_DAY)
    reg[F.STATE.value] = state
    save(ctx, key, reg)
