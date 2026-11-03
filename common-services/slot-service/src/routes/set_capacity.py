# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_CAPACITY — exact value or ±delta for one slot; never below what is booked, never above 500."""
from grepx_service import RequestContext, state_of

from domain import MAX_CAPACITY
from dto import SLOTS_TABLE, ReasonCode, SlotField as F
from .common import booked, put


def handle(ctx: RequestContext) -> None:
    slot = ctx.read.accepted_one(SLOTS_TABLE, ctx.text(F.SLOT_ID))
    if slot is None:
        return ctx.reject(ReasonCode.UNKNOWN_SLOT)
    current = int(slot.get(F.CAPACITY.value) or 0)
    value = int(ctx.get(F.VALUE)) if ctx.get(F.VALUE) is not None else current + int(ctx.get(F.DELTA, 0))
    taken = booked(ctx, slot["_key"])
    if value < taken:
        return ctx.reject(ReasonCode.BELOW_BOOKED, f"{taken} booked")
    if value > MAX_CAPACITY:
        return ctx.reject(ReasonCode.TOO_HIGH)
    put(ctx, {**state_of(slot), F.CAPACITY.value: value})
    ctx.accept({F.CAPACITY: value, F.BOOKED: taken})
