"""Booked counts and slot projection writes."""
from grepx_service import RequestContext

from dto import NOT_HOLDING, BOOKINGS_TABLE, SLOTS_TABLE, SlotField as F


def booked(ctx: RequestContext, slot_id: str) -> int:
    return sum(1 for r in ctx.read.accepted(BOOKINGS_TABLE, slot_id=slot_id) if r.get("state") not in NOT_HOLDING)


def put(ctx: RequestContext, slot: dict) -> None:
    ctx.emitter.submit(SLOTS_TABLE, slot[F.SLOT_ID.value], "ACCEPTED", slot)


def of_event(ctx: RequestContext, event_id: str) -> list[dict]:
    return sorted(ctx.read.accepted(SLOTS_TABLE, event_id=event_id), key=lambda s: s.get(F.STARTS_AT.value, ""))
