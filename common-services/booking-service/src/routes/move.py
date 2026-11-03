# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""MOVE — staff put someone in another slot (admins may overbook). The person is told the new time (unless notify=false)."""
from grepx_service import RequestContext

from dto import ReasonCode, BookingField as F
from .common import event_of, existing, save, slot_check, tell


def handle(ctx: RequestContext) -> None:
    key = ctx.text(F.BOOKING_ID)
    reg = existing(ctx, key)
    if reg is None:
        return ctx.reject(ReasonCode.NOT_REGISTERED)
    ctx.fields[F.EVENT_ID.value] = reg[F.EVENT_ID.value]
    event = event_of(ctx)
    reason, slot = slot_check(ctx, event, ctx.text(F.SLOT_ID), key, bool(ctx.get(F.OVERRIDE_CAPACITY, False)))
    if reason:
        return ctx.reject(reason)
    reg.update({F.SLOT_ID.value: slot.get("_key", ""), F.SLOT_START.value: slot.get("starts_at", ""), F.SLOT_END.value: slot.get("ends_at", "")})
    save(ctx, key, reg)
    if ctx.get("notify", True) and slot:
        tell(ctx, "booking_moved", event, reg, ref=f"move-{ctx.key}")
